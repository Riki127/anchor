import anthropic

from app.config import settings
from app.ai.adaptive import AdaptiveProvider, OutputT
from app.ai.base import ProviderResult, Usage

_MODEL = "claude-sonnet-5"


class AnthropicAIProvider(AdaptiveProvider):
    provider_name = "anthropic"

    def _parse_adaptive(
        self, prompt: str, output_format: type[OutputT]
    ) -> ProviderResult[OutputT]:
        response = self._client.messages.parse(
            model=_MODEL, max_tokens=4096,
            messages=[{"role": "user", "content": prompt}], output_format=output_format,
        )
        if response.parsed_output is None:
            raise RuntimeError("Anthropic returned no structured output")
        output = output_format.model_validate(response.parsed_output)
        usage = response.usage
        return ProviderResult(output, Usage(
            input_tokens=(usage.input_tokens + (usage.cache_read_input_tokens or 0)
                          + (usage.cache_creation_input_tokens or 0)),
            output_tokens=usage.output_tokens,
            model=response.model,
        ))

    def __init__(self, client: anthropic.Anthropic | None = None) -> None:
        if client is not None:
            self._client = client
        elif settings.anthropic_api_key:
            # Explicit key from Settings (e.g. loaded from backend/.env), since the SDK's
            # own automatic os.environ lookup can't see values pydantic-settings read
            # from a .env file rather than the real process environment.
            self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        else:
            # Falls back to the SDK's own credential resolution (ANTHROPIC_API_KEY set
            # directly in the process environment, `ant auth login`, etc.).
            self._client = anthropic.Anthropic()
