"""Purpose-specific A2A agent backed by an authenticated MCP tool endpoint."""

import contextlib
import hmac
import json
import logging
import os
from uuid import UUID

import httpx
import httpx2
from a2a.helpers import new_task_from_user_message, new_text_artifact
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import create_agent_card_routes, create_jsonrpc_routes
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities, AgentCard, AgentInterface, AgentSkill,
    TaskArtifactUpdateEvent, TaskState, TaskStatus, TaskStatusUpdateEvent,
)
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from starlette.applications import Starlette
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Mount, Route

from .argo_rest import inspect_application, inspect_workspace

logger = logging.getLogger("caipe-agent")
KIND = os.environ.get("CAIPE_AGENT_KIND", "argo")
if KIND not in {"argo", "crossplane"}:
    raise RuntimeError("Unknown CAIPE agent kind")
TOKEN = os.environ.get("CAIPE_INTERNAL_TOKEN", "")
ARGO_TOKEN = os.environ.get("ARGO_API_TOKEN", "")
ARGO_BASE = "https://argocd-server.argocd.svc.cluster.local:443"
ARGO_CA = "/etc/ai-platform-ca/ca.crt"
SERVICE_HOST = f"caipe-{KIND}-agent.ai-platform.svc.cluster.local"
MCP_URL = "http://127.0.0.1:8000/mcp"

mcp = MCPServer(name=f"ai-platform-{KIND}-tools", version="1.0.0")


if KIND == "argo":
    @mcp.tool()
    def inspect_deployment(application: str, expected_revision: str) -> dict:
        """Read one deployment Application with scoped Argo credentials."""
        try:
            result = inspect_application(
                application, base_url=ARGO_BASE, token=ARGO_TOKEN,
                expected_revision=expected_revision, ca_bundle=ARGO_CA,
            )
            logger.info("mcp.tool.inspect_deployment application=%s revision=%s status=%s",
                        application, expected_revision, result["health_status"])
            return result
        except Exception:
            logger.exception("mcp.tool.inspect_deployment.failed application=%s", application)
            raise
else:
    @mcp.tool()
    def inspect_model_workspace(application: str, workspace: str, namespace: str, request_id: str) -> dict:
        """Read one request-linked Crossplane workspace via the Argo resource API."""
        try:
            result = inspect_workspace(
                application, workspace, namespace, request_id,
                base_url=ARGO_BASE, token=ARGO_TOKEN, ca_bundle=ARGO_CA,
            )
            logger.info("mcp.tool.inspect_model_workspace request_id=%s workspace=%s ready=%s",
                        request_id, workspace, result["ready"])
            return result
        except Exception:
            logger.exception("mcp.tool.inspect_model_workspace.failed request_id=%s workspace=%s",
                             request_id, workspace)
            raise


class PlatformAgentExecutor(AgentExecutor):
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        task = context.current_task or new_task_from_user_message(context.message)
        await event_queue.enqueue_event(task)
        await event_queue.enqueue_event(TaskStatusUpdateEvent(
            task_id=context.task_id, context_id=context.context_id,
            status=TaskStatus(state=TaskState.TASK_STATE_WORKING),
        ))
        try:
            if len(context.message.parts) != 1 or not context.message.parts[0].text:
                raise ValueError("Expected one JSON text part")
            payload = json.loads(context.message.parts[0].text)
            if not isinstance(payload, dict):
                raise ValueError("Invalid task payload")
            request_id = str(UUID(payload["request_id"]))
            correlation_id = str(UUID(payload["correlation_id"]))
            if KIND == "argo":
                name = "inspect_deployment"
                arguments = {
                    "application": payload["application"],
                    "expected_revision": payload["expected_revision"],
                }
            else:
                name = "inspect_model_workspace"
                arguments = {
                    "application": payload["application"],
                    "workspace": payload["workspace"],
                    "namespace": payload["namespace"],
                    "request_id": request_id,
                }
            async with httpx2.AsyncClient(headers={"Authorization": f"Bearer {TOKEN}"}, timeout=15.0) as http_client:
                async with streamable_http_client(MCP_URL, http_client=http_client) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        tool_result = await session.call_tool(name, arguments)
            if tool_result.is_error:
                raise RuntimeError("MCP tool failed")
            result = tool_result.structured_content
            if result is None and len(tool_result.content) == 1 and hasattr(tool_result.content[0], "text"):
                result = json.loads(tool_result.content[0].text)
            if not isinstance(result, dict):
                raise RuntimeError("MCP tool returned no structured result")
            artifact = {"request_id": request_id, "correlation_id": correlation_id,
                        "agent": KIND, "status": "completed", "result": result}
            await event_queue.enqueue_event(TaskArtifactUpdateEvent(
                task_id=context.task_id, context_id=context.context_id,
                artifact=new_text_artifact(name="observation", text=json.dumps(artifact)),
            ))
            await event_queue.enqueue_event(TaskStatusUpdateEvent(
                task_id=context.task_id, context_id=context.context_id,
                status=TaskStatus(state=TaskState.TASK_STATE_COMPLETED),
            ))
            logger.info("a2a.task.completed request_id=%s correlation_id=%s agent=%s",
                        request_id, correlation_id, KIND)
        except Exception:
            logger.exception("a2a.task.failed agent=%s", KIND)
            await event_queue.enqueue_event(TaskArtifactUpdateEvent(
                task_id=context.task_id, context_id=context.context_id,
                artifact=new_text_artifact(name="error", text=json.dumps({
                    "agent": KIND, "status": "failed", "error": "observation_failed",
                })),
            ))
            await event_queue.enqueue_event(TaskStatusUpdateEvent(
                task_id=context.task_id, context_id=context.context_id,
                status=TaskStatus(state=TaskState.TASK_STATE_FAILED),
            ))

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise NotImplementedError("Read-only observation tasks cannot be cancelled")


skill = AgentSkill(
    id=f"inspect_{KIND}", name=f"Inspect {KIND} deployment state",
    description="Read request-scoped live platform state", tags=["platform", KIND],
    examples=["Check my deployment status"],
)
card = AgentCard(
    name=f"AI Platform {KIND.title()} Agent",
    description="Purpose-specific read-only deployment observation agent",
    version="1.0.0", default_input_modes=["application/json"],
    default_output_modes=["application/json"],
    capabilities=AgentCapabilities(streaming=False),
    supported_interfaces=[AgentInterface(
        protocol_binding="JSONRPC", url=f"http://{SERVICE_HOST}:8000/rpc",
        protocol_version="1.0",
    )], skills=[skill],
)
handler = DefaultRequestHandler(
    agent_executor=PlatformAgentExecutor(), task_store=InMemoryTaskStore(),
    agent_card=card,
)


async def health(_request):
    return JSONResponse({"status": "ok", "agent": KIND})


routes = [Route("/health", health)]
routes.extend(create_agent_card_routes(card))
routes.extend(create_jsonrpc_routes(handler, "/rpc"))
routes.append(Mount("/mcp", mcp.streamable_http_app(
    streamable_http_path="/", json_response=True, stateless_http=True,
    transport_security=TransportSecuritySettings(
        allowed_hosts=["127.0.0.1:*", "localhost:*", f"{SERVICE_HOST}:*"],
    ),
)))


@contextlib.asynccontextmanager
async def lifespan(_app):
    async with mcp.session_manager.run():
        yield


application = Starlette(routes=routes, lifespan=lifespan)


class InternalAuth:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and (scope["path"].startswith("/rpc") or scope["path"].startswith("/mcp")):
            headers = dict(scope.get("headers", []))
            presented = headers.get(b"authorization", b"").decode()
            expected = f"Bearer {TOKEN}"
            if not TOKEN or not hmac.compare_digest(presented, expected):
                await PlainTextResponse("Unauthorized", status_code=401)(scope, receive, send)
                return
        await self.app(scope, receive, send)


app = InternalAuth(application)
