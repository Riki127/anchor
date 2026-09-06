from app.ai.base import AIProvider, ProviderResult
from app.models import AIUsage
from sqlmodel import Session


def record_usage(db: Session, result: ProviderResult, provider: AIProvider, operation: str,
                 *, role_id: int | None = None, session_id: int | None = None) -> None:
    db.add(AIUsage(role_id=role_id, session_id=session_id, operation=operation,
                   provider=provider.provider_name, model=result.usage.model,
                   input_tokens=result.usage.input_tokens, output_tokens=result.usage.output_tokens))
