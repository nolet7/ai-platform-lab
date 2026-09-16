from ai_gateway.providers.base import AIProvider
from ai_gateway.providers.mock import MockProvider

_PROVIDERS: dict[str, AIProvider] = {
    "mock-primary": MockProvider(
        provider_name="mock-primary",
        fail_marker="SIMULATE_PRIMARY_FAILURE",
    ),
    "mock-secondary": MockProvider(
        provider_name="mock-secondary",
    ),
}


def get_provider(name: str) -> AIProvider | None:
    return _PROVIDERS.get(name)
