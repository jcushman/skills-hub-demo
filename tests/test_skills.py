"""Skill evaluation tests.

Each test discovers rubric.yaml files alongside SKILL.md files, runs the
test scenarios against configured models, and evaluates the conversation
traces using judge models.

Run with:
    uv run pytest tests/ -v -s          # skip scenarios that already have traces
    uv run pytest tests/ -v -s --rerun  # force re-run everything

Requires OPENROUTER_API_KEY in .env (or the env var configured in test_config.yaml).
"""

from __future__ import annotations

import pytest

from harness.evaluator import AntiPatternResult, evaluate_trace
from harness.runner import ModelConfig, run_scenario
from harness.trace_writer import save_trace, trace_exists

MINIMUM_SCORE = 50
NULL_VERSION = "_null"


def _skip_if_exists(request, skill: str, version: str, scenario_id: str, model: str):
    """Skip this test if a trace already exists, unless --rerun was passed."""
    if request.config.getoption("--rerun"):
        return
    if trace_exists(skill, version, scenario_id, model):
        pytest.skip(f"Trace exists for {skill}/{version}/{scenario_id} ({model}) — use --rerun to force")


def _run_and_evaluate(
    *,
    openai_client,
    model: ModelConfig,
    judge_models: list[ModelConfig],
    rubric: dict,
    scenario: dict,
    system_prompt: str,
    skill_name: str,
    persona: str,
    version: str,
    minimum_score: int = MINIMUM_SCORE,
):
    """Run a scenario, evaluate it, save the trace, and assert quality."""
    trace = run_scenario(
        client=openai_client,
        model_config=model,
        system_prompt=system_prompt,
        scenario=scenario,
        skill_name=skill_name,
    )

    assert len(trace.agent_turns()) > 0, "Model produced no responses"

    for judge in judge_models:
        report = evaluate_trace(
            client=openai_client,
            judge=judge,
            rubric=rubric,
            trace=trace,
        )

        print(f"\n{report.summary()}\n")

        save_trace(
            trace,
            report,
            persona=persona,
            version=version,
            scenario=scenario,
            model_config=model,
            judge_config=judge,
        )

        assert not report.has_anti_pattern_violations(), (
            f"Anti-pattern violations detected:\n"
            + "\n".join(
                f"  {c.criterion_id}: {c.justification}"
                for c in report.anti_patterns
                if c.result == AntiPatternResult.VIOLATION.value
            )
        )

        score = report.score()
        assert score >= minimum_score, (
            f"Score {score:.0f} below minimum {minimum_score}\n{report.summary()}"
        )


@pytest.mark.parametrize("model_idx", [0], indirect=False)
def test_skill_scenario(
    request,
    rubric_scenario: dict,
    openai_client,
    models_under_test: list[ModelConfig],
    judge_models: list[ModelConfig],
    model_idx: int,
):
    """Run a skill scenario and evaluate the conversation against the rubric."""
    if model_idx >= len(models_under_test):
        pytest.skip(f"Model index {model_idx} out of range")

    model = models_under_test[model_idx]
    skill_name = rubric_scenario["skill_name"]
    version = rubric_scenario["version"]
    scenario = rubric_scenario["scenario"]

    _skip_if_exists(request, skill_name, version, scenario["id"], model.model)

    _run_and_evaluate(
        openai_client=openai_client,
        model=model,
        judge_models=judge_models,
        rubric=rubric_scenario["rubric"],
        scenario=scenario,
        system_prompt=rubric_scenario["system_prompt"],
        skill_name=skill_name,
        persona=rubric_scenario["persona"],
        version=version,
    )


@pytest.mark.parametrize("model_idx", [0], indirect=False)
def test_null_scenario(
    request,
    rubric_scenario: dict,
    openai_client,
    models_under_test: list[ModelConfig],
    judge_models: list[ModelConfig],
    model_idx: int,
):
    """Run the same scenario with NO skill — a bare-model baseline.

    Null baselines let you measure whether the skill is actually adding value.
    They use version '_null' in the trace index and are not expected to pass
    the same quality bar as skilled tests (minimum_score=0 so they always
    record but never fail the suite).
    """
    if model_idx >= len(models_under_test):
        pytest.skip(f"Model index {model_idx} out of range")

    model = models_under_test[model_idx]
    skill_name = rubric_scenario["skill_name"]
    scenario = rubric_scenario["scenario"]

    _skip_if_exists(request, skill_name, NULL_VERSION, scenario["id"], model.model)

    _run_and_evaluate(
        openai_client=openai_client,
        model=model,
        judge_models=judge_models,
        rubric=rubric_scenario["rubric"],
        scenario=scenario,
        system_prompt="You are a helpful assistant.",
        skill_name=skill_name,
        persona=rubric_scenario["persona"],
        version=NULL_VERSION,
        minimum_score=0,
    )
