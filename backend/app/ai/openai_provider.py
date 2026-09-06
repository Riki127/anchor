from openai import OpenAI

from app.config import settings
from app.ai.adaptive import AdaptiveProvider, OutputT
from app.ai.base import ProviderResult, Usage


class OpenAIProvider(AdaptiveProvider):
    provider_name = "openai"

    def _parse_adaptive(
        self, prompt: str, output_format: type[OutputT]
    ) -> ProviderResult[OutputT]:
        response = self._client.responses.parse(
            model=settings.openai_model, input=prompt, text_format=output_format, store=False,
        )
        if response.output_parsed is None:
            raise RuntimeError("OpenAI returned no structured output")
        output = output_format.model_validate(response.output_parsed)
        return ProviderResult(output, Usage(
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            model=response.model,
        ))

    def __init__(self, client: OpenAI | None = None) -> None:
        if client is not None:
            self._client = client
        elif settings.openai_api_key:
            self._client = OpenAI(api_key=settings.openai_api_key)
        else:
            self._client = OpenAI()
