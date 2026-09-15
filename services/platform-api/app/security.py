import os
from collections.abc import Callable

import jwt
from fastapi import Depends, HTTPException, status
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
    PyJWKClientError,
)
from pydantic import BaseModel


OIDC_ISSUER = os.getenv(
    "OIDC_ISSUER",
    "http://localhost:8081/realms/ai-platform",
)

OIDC_AUDIENCE = os.getenv(
    "OIDC_AUDIENCE",
    "ai-platform-api",
)

OIDC_JWKS_URL = os.getenv(
    "OIDC_JWKS_URL",
    f"{OIDC_ISSUER}/protocol/openid-connect/certs",
)

JWT_ALGORITHMS = ["RS256"]

bearer_scheme = HTTPBearer(
    scheme_name="KeycloakBearer",
    bearerFormat="JWT",
    auto_error=True,
)

jwks_client = PyJWKClient(
    OIDC_JWKS_URL,
    cache_keys=True,
)


class Principal(BaseModel):
    subject: str
    username: str
    tenant_id: str
    roles: list[str]


def authentication_error(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={
            "WWW-Authenticate": "Bearer",
        },
    )


def get_current_principal(
    credentials: HTTPAuthorizationCredentials = Depends(
        bearer_scheme
    ),
) -> Principal:

    token = credentials.credentials

    try:
        signing_key = jwks_client.get_signing_key_from_jwt(
            token
        )

        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=JWT_ALGORITHMS,
            audience=OIDC_AUDIENCE,
            issuer=OIDC_ISSUER,
            options={
                "require": [
                    "exp",
                    "iat",
                    "iss",
                    "sub",
                ]
            },
        )

    except ExpiredSignatureError:
        raise authentication_error(
            "Access token has expired"
        )

    except InvalidAudienceError:
        raise authentication_error(
            "Invalid token audience"
        )

    except InvalidIssuerError:
        raise authentication_error(
            "Invalid token issuer"
        )

    except PyJWKClientError:
        raise authentication_error(
            "Unable to resolve JWT signing key"
        )

    except InvalidTokenError:
        raise authentication_error(
            "Invalid access token"
        )

    tenant_id = claims.get("tenant_id")

    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token does not contain tenant_id",
        )

    roles = (
        claims
        .get("realm_access", {})
        .get("roles", [])
    )

    username = claims.get(
        "preferred_username",
        claims["sub"],
    )

    return Principal(
        subject=claims["sub"],
        username=username,
        tenant_id=tenant_id,
        roles=roles,
    )


def require_any_role(
    *required_roles: str,
) -> Callable:

    def role_dependency(
        principal: Principal = Depends(
            get_current_principal
        ),
    ) -> Principal:

        if "platform-admin" in principal.roles:
            return principal

        user_roles = set(principal.roles)
        required = set(required_roles)

        if not required.intersection(user_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "message": "Insufficient permissions",
                    "required_any_of": list(
                        required_roles
                    ),
                },
            )

        return principal

    return role_dependency
