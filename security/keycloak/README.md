# AI Platform Keycloak Security

This module configures Keycloak authentication and authorization for the
Self-Service AI/ML Deployment Control Plane.

## Realm

ai-platform

## OIDC Client

ai-platform-api

## Realm Roles

- platform-admin
- ml-engineer
- data-scientist
- inference-client

## Machine Identity

service-account-ai-platform-api

The service account receives the:

inference-client

realm role.

## Authentication

OAuth 2.0 Client Credentials Grant

Client authentication:

HTTP Basic authentication

## JWT Security

Expected properties:

- algorithm: RS256
- issuer: ai-platform realm
- audience: ai-platform-api
- authorized party: ai-platform-api
- service account: service-account-ai-platform-api
- realm role: inference-client

## JWKS

FastAPI and other APIs will use the Keycloak JWKS endpoint to validate
token signatures.

## Local Ports

| Port | Service |
|------|---------|
| 8080 | Argo CD |
| 18080 | Keycloak |

Never assign Keycloak to local port 8080 while the Argo CD port-forward
is running.

## Configure Phase 2K

From:

~/ai-platform-lab/security/keycloak

Run:

./scripts/run-phase-2k.sh

## Start Keycloak Port Forward

./scripts/08-port-forward.sh

## Stop Keycloak Port Forward

./scripts/stop-port-forward.sh

## Test Client Credentials

./scripts/09-token-test.sh

## Validate JWT Claims

./scripts/10-validate-token.sh

## Validate JWKS

./scripts/11-jwks-test.sh

## Security Rules

Never commit:

- client secrets
- access tokens
- refresh tokens
- admin passwords
- generated runtime credential files
