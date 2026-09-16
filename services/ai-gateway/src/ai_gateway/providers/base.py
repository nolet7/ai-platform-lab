from abc import ABC, abstractmethod
from dataclasses import dataclass

from ai_gateway.models import AIRequest


class ProviderError(RuntimeError):
    """Raised when an AI provider invocation fails."""


@dataclass
class ProviderResult:
    provider: str
    model: str
    output: str
    input_tokens: int
    output_tokens: int


class AIProvider(ABC):

    @abstractmethod
    async def generate(
        self,
        request: AIRequest,
        model: str,
        max_output_tokens: int,
    ) -> ProviderResult:
        raise NotImplementedError
