from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class HavenSupportSource:
    source_id: str
    title: str
    intent: str


@dataclass(frozen=True, slots=True)
class HavenHandoffPayload:
    intent: str
    status: str
    context: str
    reason: str
    next_step: str


@dataclass(frozen=True, slots=True)
class HavenSupportOutput:
    message: str
    normalized_message: str
    channel: str
    intent: str
    action: str
    answer: str
    next_steps: list[str]
    boundary_rules: list[str]
    sources: list[HavenSupportSource]
    handoff: HavenHandoffPayload | None
