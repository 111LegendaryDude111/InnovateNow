from __future__ import annotations

from fastapi import HTTPException
from pydantic import BaseModel

from .haven_support_bot import HavenSupportBot, get_haven_support_bot


class HavenSupportRequest(BaseModel):
    message: str
    channel: str = "help_center"


class HavenSupportSourceResponse(BaseModel):
    source_id: str
    title: str
    intent: str


class HavenHandoffPayloadResponse(BaseModel):
    intent: str
    status: str
    context: str
    reason: str
    next_step: str


class HavenSupportResponse(BaseModel):
    message: str
    normalized_message: str
    channel: str
    intent: str
    action: str
    answer: str
    next_steps: list[str]
    boundary_rules: list[str]
    sources: list[HavenSupportSourceResponse]
    handoff: HavenHandoffPayloadResponse | None


def respond_to_haven_support(request: HavenSupportRequest) -> HavenSupportResponse:
    """Возвращает policy-aware ответ Haven support bot."""
    return create_haven_support_response(request)


def create_haven_support_response(
    request: HavenSupportRequest,
    *,
    bot: HavenSupportBot | None = None,
) -> HavenSupportResponse:
    """Создает API response без LLM/network вызовов."""
    try:
        output = (bot or get_haven_support_bot()).respond(
            request.message,
            channel=request.channel,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    handoff = None
    if output.handoff is not None:
        handoff = HavenHandoffPayloadResponse(
            intent=output.handoff.intent,
            status=output.handoff.status,
            context=output.handoff.context,
            reason=output.handoff.reason,
            next_step=output.handoff.next_step,
        )
    return HavenSupportResponse(
        message=output.message,
        normalized_message=output.normalized_message,
        channel=output.channel,
        intent=output.intent,
        action=output.action,
        answer=output.answer,
        next_steps=output.next_steps,
        boundary_rules=output.boundary_rules,
        sources=[
            HavenSupportSourceResponse(
                source_id=source.source_id,
                title=source.title,
                intent=source.intent,
            )
            for source in output.sources
        ],
        handoff=handoff,
    )
