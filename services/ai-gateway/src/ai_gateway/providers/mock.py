from ai_gateway.config import settings
from ai_gateway.models import AIRequest
from ai_gateway.providers.base import (
    AIProvider,
    ProviderError,
    ProviderResult,
)


class MockProvider(AIProvider):

    def __init__(
        self,
        provider_name: str,
        fail_marker: str | None = None,
    ):
        self.provider_name = provider_name
        self.fail_marker = fail_marker

    async def generate(
        self,
        request: AIRequest,
        model: str,
        max_output_tokens: int,
    ) -> ProviderResult:

        if (
            settings.failure_injection_enabled
            and self.fail_marker
            and self.fail_marker.lower()
            in request.prompt.lower()
        ):
            raise ProviderError(
                f"Simulated failure for {self.provider_name}"
            )

        output = (
            f"[MOCK AI RESPONSE] "
            f"provider={self.provider_name}; "
            f"use_case={request.use_case}; "
            f"classification={request.data_classification}; "
            f"prompt={request.prompt}"
        )

        return ProviderResult(
            provider=self.provider_name,
            model=model,
            output=output,
            input_tokens=len(request.prompt.split()),
            output_tokens=len(output.split()),
        )
