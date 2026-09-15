# AI Platform API - Phase 2L

Phase 2L connects the AI Platform API to Keycloak.

## Security controls

The service validates:

- Bearer authentication
- RS256 JWT signatures
- Keycloak JWKS signing keys
- issuer
- audience
- expiration
- authorized party
- realm roles

## Realm

ai-platform

## OAuth client

ai-platform-api

## Machine identity

service-account-ai-platform-api

## Required inference role

inference-client

## Ports

| Port | Component |
|------|-----------|
| 8080 | Argo CD |
| 18080 | Keycloak |
| 8001 | AI Platform FastAPI |

## Public endpoints

GET /health/live

GET /health/ready

## Authenticated endpoints

GET /api/v1/whoami

## RBAC protected endpoints

POST /api/v1/inference

Required role:

inference-client

or

platform-admin

## Run

Ensure Keycloak port-forward is running:

cd ~/ai-platform-lab/security/keycloak

./scripts/08-port-forward.sh

Then:

cd ~/ai-platform-lab/services/ai-platform-api

source .venv/bin/activate

./scripts/start.sh

## Swagger

http://127.0.0.1:8001/docs

## Security smoke test

./scripts/smoke-test.sh
