from collections.abc import Callable

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient
from jwt.exceptions import (
    ExpiredSignatureError,
    InvalidAudienceError,
    InvalidIssuerError,
    InvalidTokenError,
)

from app.config import settings
from app.schemas import TokenIdentity


bearer_scheme = HTTPBearer(
    auto_error=False,
    scheme_name="KeycloakBearer",
)


jwks_client = PyJWKClient(
    settings.keycloak_jwks_url,
    cache_keys=True,
)


def unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def extract_roles(payload: dict) -> list[str]:
    realm_access = payload.get("realm_access", {})

    if not isinstance(realm_access, dict):
        return []

    roles = realm_access.get("roles", [])

    if not isinstance(roles, list):
        return []

    return roles


def decode_access_token(token: str) -> dict:
    try:
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=[settings.keycloak_algorithm],
            audience=settings.keycloak_audience,
            issuer=settings.keycloak_issuer,
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
        raise unauthorized("Access token has expired") from exc

    except InvalidAudienceError as exc:
        raise unauthorized("Invalid token audience") from exc

    except InvalidIssuerError as exc:
        raise unauthorized("Invalid token issuer") from exc

    except InvalidTokenError as exc:
        raise unauthorized("Invalid access token") from exc

    except Exception as exc:
        raise unauthorized("Unable to validate access token") from exc


async def get_current_identity(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
) -> TokenIdentity:

    if credentials is None:
        raise unauthorized("Bearer token required")

    if credentials.scheme.lower() != "bearer":
        raise unauthorized("Bearer authentication required")

    payload = decode_access_token(credentials.credentials)

    return TokenIdentity(
        subject=payload.get("sub"),
        username=payload.get("preferred_username"),
        client_id=payload.get("azp"),
        audience=payload.get("aud"),
        roles=extract_roles(payload),
    )


def require_roles(*required_roles: str) -> Callable:

    async def dependency(
        identity: TokenIdentity = Depends(get_current_identity),
    ) -> TokenIdentity:

        identity_roles = set(identity.roles)
        required = set(required_roles)

        if not identity_roles.intersection(required):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "message": "Insufficient permissions",
                    "required_roles": sorted(required),
                    "assigned_roles": sorted(identity_roles),
                },
            )

        return identity

    return dependency
