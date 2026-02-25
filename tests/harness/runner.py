"""Run a conversation between a model and a simulated user following a test scenario.

The runner sends the skill as a system prompt, then plays out the scripted user
messages from the test scenario, capturing the full conversation trace. Between
each user message the model responds, producing an interleaved transcript.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from openai import OpenAI

log = logging.getLogger("harness.runner")


@dataclass
class ModelConfig:
    id: str
    model: str
    temperature: float = 0.3
    max_tokens: int = 2048


@dataclass
class Message:
    role: str
    content: str


@dataclass
class ConversationTrace:
    skill_name: str
    scenario_id: str
    model_id: str
    messages: list[Message] = field(default_factory=list)

    def agent_turns(self) -> list[Message]:
        return [m for m in self.messages if m.role == "assistant"]

    def user_turns(self) -> list[Message]:
        return [m for m in self.messages if m.role == "user"]

    def as_transcript(self) -> str:
        lines = []
        for m in self.messages:
            label = "USER" if m.role == "user" else "AGENT"
            lines.append(f"[{label}]\n{m.content}\n")
        return "\n".join(lines)


def load_skill_as_system_prompt(skill_path: Path) -> str:
    """Read a SKILL.md and return it as a system prompt string."""
    text = skill_path.read_text(encoding="utf-8")
    return (
        "You are an AI agent with the following skill installed. "
        "Follow its instructions precisely.\n\n"
        f"{text}"
    )


def run_scenario(
    client: OpenAI,
    model_config: ModelConfig,
    system_prompt: str,
    scenario: dict,
    skill_name: str,
) -> ConversationTrace:
    """Run a single test scenario and return the conversation trace.

    The scenario dict should have 'id', 'setup', 'messages', and 'expected'
    keys as defined in the rubric schema.
    """
    trace = ConversationTrace(
        skill_name=skill_name,
        scenario_id=scenario["id"],
        model_id=model_config.id,
    )

    setup_context = scenario.get("setup", "")
    user_messages = scenario["messages"]
    log.info(
        "Running scenario %s (%d user turns) with model %s",
        scenario["id"], len(user_messages), model_config.model,
    )

    openai_messages: list[dict] = [{"role": "system", "content": system_prompt}]

    if setup_context:
        log.info("  Setup: %s", setup_context.strip()[:120])
        openai_messages.append({
            "role": "system",
            "content": f"Context about the user you are helping: {setup_context}",
        })

    for i, user_msg in enumerate(user_messages, 1):
        content = user_msg["content"]
        log.info("  [Turn %d/%d] USER: %s", i, len(user_messages), content[:120])
        openai_messages.append({"role": "user", "content": content})
        trace.messages.append(Message(role="user", content=content))

        log.debug("  Calling %s ...", model_config.model)
        response = client.chat.completions.create(
            model=model_config.model,
            messages=openai_messages,
            temperature=model_config.temperature,
            max_tokens=model_config.max_tokens,
        )

        assistant_content = response.choices[0].message.content or ""
        usage = response.usage
        tokens_info = (
            f" ({usage.prompt_tokens}+{usage.completion_tokens} tokens)"
            if usage else ""
        )
        preview = assistant_content.replace("\n", " ")[:150]
        log.info("  [Turn %d/%d] AGENT:%s %s", i, len(user_messages), tokens_info, preview)
        openai_messages.append({"role": "assistant", "content": assistant_content})
        trace.messages.append(Message(role="assistant", content=assistant_content))

    log.info("  Conversation complete: %d turns total", len(trace.messages))
    return trace


def load_test_config(config_path: Path) -> dict:
    """Load the test_config.yaml file."""
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)
