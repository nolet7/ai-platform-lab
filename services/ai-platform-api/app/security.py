import logging
from collections.abc import Callable

import jwt
from fastapi import (
    Depends,
    HTTPException,
    Request,
    status,
)
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from jwt import PyJWKClient
from jwt.exceptions import (
    ExpiredSignatureError,
    InvalidAudienceError,
    InvalidIssuerError,
    InvalidTokenError,
)

from app.config import settings
from app.observability import (
    AUTHENTICATED_REQUESTS,
    AUTH_FAILURES,
    RBAC_DENIALS,
)
from app.schemas import TokenIdentity


logger = logging.getLogger("ai-platform-api.security")


bearer_scheme = HTTPBearer(
    auto_error=False,
    scheme_name="KeycloakBearer",
)


jwks_client = PyJWKClient(
    settings.keycloak_jwks_url,
    cache_keys=True,
)


def unauthorized(
    reason: str,
    detail: str,
) -> HTTPException:

    AUTH_FAILURES.labels(
        reason=reason
    ).inc()

    logger.warning(
        "authentication_failed",
        extra={
            "event": "authentication_failed",
            "reason": reason,
        },
    )

    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={
            "WWW-Authenticate": "Bearer"
        },
    )


def extract_roles(
    payload: dict,
) -> list[str]:

    realm_access = payload.get(
        "realm_access",
        {},
    )

    if not isinstance(
        realm_access,
        dict,
    ):
        return []

    roles = realm_access.get(
        "roles",
        [],
    )

    if not isinstance(
        roles,
        list,
    ):
        return []

    return roles


def decode_access_token(
    token: str,
) -> dict:

    try:
        signing_key = (
            jwks_client
            .get_signing_key_from_jwt(
                token
            )
        )

        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=[
                settings.keycloak_algorithm
            ],
            audience=(
                settings.keycloak_audience
            ),
            issuer=(
                settings.keycloak_issuer
            ),
            options={
                "require": [
                    "exp",
                    "iat",
                    "iss",
                    "aud",
                ]
            },
        )

        return payload

    except ExpiredSignatureError as exc:
        raise unauthorized(
            "expired_token",
            "Access token has expired",
        ) from exc

    except InvalidAudienceError as exc:
        raise unauthorized(
            "invalid_audience",
            "Invalid token audience",
        ) from exc

    except InvalidIssuerError as exc:
        raise unauthorized(
            "invalid_issuer",
            "Invalid token issuer",
        ) from exc

    except InvalidTokenError as exc:
        raise unauthorized(
            "invalid_token",
            "Invalid access token",
        ) from exc

    except Exception as exc:
        raise unauthorized(
            "validation_error",
            "Unable to validate access token",
        ) from exc


async def get_current_identity(
    request: Request,
    credentials: (
        HTTPAuthorizationCredentials | None
    ) = Depends(
        bearer_scheme
    ),
) -> TokenIdentity:

    if credentials is None:
        raise unauthorized(
            "missing_token",
            "Bearer token required",
        )

    if (
        credentials.scheme.lower()
        != "bearer"
    ):
        raise unauthorized(
            "invalid_scheme",
            "Bearer authentication required",
        )

    payload = decode_access_token(
        credentials.credentials
    )

    identity = TokenIdentity(
        subject=payload.get("sub"),
        username=payload.get(
            "preferred_username"
        ),
        client_id=payload.get("azp"),
        audience=payload.get("aud"),
        roles=extract_roles(
            payload
        ),
    )

    AUTHENTICATED_REQUESTS.labels(
        client_id=(
            identity.client_id
            or "unknown"
        )
    ).inc()

    logger.info(
        "authentication_success",
        extra={
            "event": "authentication_success",
            "request_id": getattr(
                request.state,
                "request_id",
                None,
            ),
            "client_id": identity.client_id,
            "username": identity.username,
        },
    )

    return identity


def require_roles(
    *required_roles: str,
) -> Callable:

    async def dependency(
        request: Request,
        identity: TokenIdentity = Depends(
            get_current_identity
        ),
    ) -> TokenIdentity:

        identity_roles = set(
            identity.roles
        )

        required = set(
            required_roles
        )

        if not identity_roles.intersection(
            required
        ):
            RBAC_DENIALS.labels(
                route=request.url.path
            ).inc()

            logger.warning(
                "rbac_denied",
                extra={
                    "event": "rbac_denied",
                    "request_id": getattr(
                        request.state,
                        "request_id",
                        None,
                    ),
                    "path": request.url.path,
                    "client_id": (
                        identity.client_id
                    ),
                    "username": (
                        identity.username
                    ),
                    "required_roles": (
                        sorted(required)
                    ),
                    "assigned_roles": (
                        sorted(
                            identity_roles
                        )
                    ),
                },
            )

            raise HTTPException(
                status_code=(
                    status.HTTP_403_FORBIDDEN
                ),
                detail={
                    "message":
                        "Insufficient permissions",
                    "required_roles":
                        sorted(required),
                    "assigned_roles":
                        sorted(identity_roles),
                },
            )

        return identity

    return dependency
