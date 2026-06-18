from __future__ import annotations

import re
from typing import Any

from .haven_support_config import DEFAULT_HAVEN_SUPPORT_PATH, load_haven_support_config
from .haven_support_models import (
    HavenHandoffPayload,
    HavenSupportOutput,
    HavenSupportSource,
)
SUPPORTED_CHANNELS = {"help_center", "in_app"}


class HavenSupportBot:
    def __init__(self, *, config_path=DEFAULT_HAVEN_SUPPORT_PATH, config: dict[str, Any] | None = None) -> None:
        self._config = config or load_haven_support_config(config_path)

    def respond(self, message: str, *, channel: str = "help_center") -> HavenSupportOutput:
        message_text = _require_message(message)
        support_channel = _require_channel(channel)
        normalized = _normalize(message_text)
        route = _route_for_message(self._config, normalized)
        if route is None:
            return _fallback_response(self._config, message_text, normalized, support_channel)
        if route["route"] == "answer":
            return _answer_response(self._config, route, message_text, normalized, support_channel)
        if route["route"] == "escalate":
            return _escalation_response(self._config, route, message_text, normalized, support_channel)
        return _refusal_response(self._config, route, message_text, normalized, support_channel)


def _answer_response(config: dict[str, Any], route: dict[str, Any], message: str, normalized: str, channel: str) -> HavenSupportOutput:
    entries = [_entry_by_id(config, entry_id) for entry_id in route["entry_ids"]]
    answer = "\n\n".join(entry["answer"] for entry in entries)
    return HavenSupportOutput(
        message=message,
        normalized_message=normalized,
        channel=channel,
        intent=route["intent"],
        action="answer",
        answer=answer,
        next_steps=_flow_steps(config, route["intent"]),
        boundary_rules=list(config["boundary_rules"]),
        sources=[
            HavenSupportSource(entry["id"], entry["title"], entry["intent"])
            for entry in entries
        ],
        handoff=None,
    )


def _escalation_response(config: dict[str, Any], route: dict[str, Any], message: str, normalized: str, channel: str) -> HavenSupportOutput:
    answer = (
        "I need to hand this to Haven support. I can keep the context, but a "
        "human specialist must handle identity, safety, billing action, or "
        "hardware replacement cases."
    )
    return HavenSupportOutput(
        message=message,
        normalized_message=normalized,
        channel=channel,
        intent=route["intent"],
        action="escalate",
        answer=answer,
        next_steps=[route["next_step"]],
        boundary_rules=list(config["boundary_rules"]),
        sources=[],
        handoff=HavenHandoffPayload(
            intent=route["intent"],
            status="needs_human",
            context=message,
            reason=route["reason"],
            next_step=route["next_step"],
        ),
    )


def _refusal_response(config: dict[str, Any], route: dict[str, Any], message: str, normalized: str, channel: str) -> HavenSupportOutput:
    return HavenSupportOutput(
        message=message,
        normalized_message=normalized,
        channel=channel,
        intent=route["intent"],
        action="refuse",
        answer=route["answer"],
        next_steps=["Ask about Haven setup, monitoring, billing, account, or troubleshooting."],
        boundary_rules=list(config["boundary_rules"]),
        sources=[],
        handoff=None,
    )


def _fallback_response(config: dict[str, Any], message: str, normalized: str, channel: str) -> HavenSupportOutput:
    return HavenSupportOutput(
        message=message,
        normalized_message=normalized,
        channel=channel,
        intent="unknown",
        action="clarify",
        answer=(
            "I can help with Haven device setup, monitoring plans, billing policy, "
            "account workflows, and basic troubleshooting. Please rephrase the "
            "request within those support areas."
        ),
        next_steps=["Rephrase as a Haven support question or contact Haven support."],
        boundary_rules=list(config["boundary_rules"]),
        sources=[],
        handoff=None,
    )


def _route_for_message(config: dict[str, Any], normalized: str) -> dict[str, Any] | None:
    for group in ("escalation_requests", "unsupported_requests", "supported_requests"):
        route = _best_route(config[group], normalized)
        if route is not None:
            return route
    return None


def _best_route(routes: list[dict[str, Any]], normalized: str) -> dict[str, Any] | None:
    scored = [
        (sum(_contains_keyword(normalized, keyword) for keyword in route["keywords"]), route)
        for route in routes
    ]
    score, route = max(scored, key=lambda item: item[0])
    return route if score > 0 else None


def _contains_keyword(normalized: str, keyword: str) -> bool:
    clean_keyword = _normalize(keyword)
    return f" {clean_keyword} " in f" {normalized} "


def _entry_by_id(config: dict[str, Any], entry_id: str) -> dict[str, Any]:
    return next(entry for entry in config["knowledge"] if entry["id"] == entry_id)


def _flow_steps(config: dict[str, Any], intent: str) -> list[str]:
    flow = next(item for item in config["flows"] if item["intent"] == intent)
    return list(flow["steps"])


def _require_message(message: str) -> str:
    clean = message.strip()
    if not clean:
        raise ValueError("message must be a non-empty string")
    return clean


def _require_channel(channel: str) -> str:
    clean = channel.strip()
    if clean not in SUPPORTED_CHANNELS:
        raise ValueError("channel must be help_center or in_app")
    return clean


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", text.lower())).strip()


_haven_support_bot: HavenSupportBot | None = None


def get_haven_support_bot() -> HavenSupportBot:
    global _haven_support_bot
    if _haven_support_bot is None:
        # ponytail: process-local config cache; admin CMS belongs in real ops work.
        _haven_support_bot = HavenSupportBot()
    return _haven_support_bot
