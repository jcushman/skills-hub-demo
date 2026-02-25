"""Fixtures for skill testing.

Discovers rubric.yaml files across the skills directory and provides them
as parametrized test cases, along with configured OpenAI clients and model
configs from test_config.yaml.
"""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path

import pytest
import yaml
from dotenv import load_dotenv
from openai import OpenAI

from harness.runner import ModelConfig, load_skill_as_system_prompt
from harness.trace_writer import rebuild_index

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = PROJECT_ROOT / "skills"
TESTS_DIR = Path(__file__).resolve().parent


def pytest_addoption(parser):
    parser.addoption(
        "--rerun", action="store_true", default=False,
        help="Re-run scenarios even if a trace already exists in the index.",
    )


def pytest_configure(config):
    """Set up logging for the test harness so output streams in real time with -s."""
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(name)s | %(message)s"))
    harness_logger = logging.getLogger("harness")
    harness_logger.addHandler(handler)
    harness_logger.setLevel(logging.DEBUG if config.option.verbose > 1 else logging.INFO)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def pytest_sessionfinish(session, exitstatus):
    """Rebuild the trace index after all tests complete.

    With pytest-xdist, only the controller node rebuilds the index (workers
    have a 'workerinput' attribute on their config).
    """
    if hasattr(session.config, "workerinput"):
        return
    rebuild_index()


def _extract_version(skill_path: Path) -> str:
    """Pull the version from SKILL.md YAML frontmatter."""
    text = skill_path.read_text(encoding="utf-8")
    m = re.search(r"version:\s*(.+)", text)
    return m.group(1).strip() if m else "0.0.0"


def discover_rubrics() -> list[dict]:
    """Find all rubric.yaml files and pair them with their SKILL.md."""
    rubrics = []
    for rubric_path in sorted(SKILLS_DIR.rglob("rubric.yaml")):
        skill_md = rubric_path.parent / "SKILL.md"
        if not skill_md.exists():
            continue
        with open(rubric_path, encoding="utf-8") as f:
            rubric = yaml.safe_load(f)
        rubric["_rubric_path"] = rubric_path
        rubric["_skill_path"] = skill_md
        rubric["_version"] = _extract_version(skill_md)
        rubrics.append(rubric)
    return rubrics


def load_test_config() -> dict:
    config_path = TESTS_DIR / "test_config.yaml"
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="session")
def test_config() -> dict:
    return load_test_config()


@pytest.fixture(scope="session")
def openai_client(test_config) -> OpenAI:
    load_dotenv(PROJECT_ROOT / ".env")
    api_config = test_config.get("api", {})
    api_key = os.environ.get(api_config.get("api_key_env", "OPENROUTER_API_KEY"), "")
    if not api_key:
        pytest.skip("No API key configured -- set OPENROUTER_API_KEY in .env")
    return OpenAI(
        api_key=api_key,
        base_url=api_config.get("base_url", "https://openrouter.ai/api/v1"),
        timeout=60.0,
        max_retries=1,
    )


@pytest.fixture(scope="session")
def models_under_test(test_config) -> list[ModelConfig]:
    return [
        ModelConfig(**cfg) for cfg in test_config.get("models_under_test", [])
    ]


@pytest.fixture(scope="session")
def judge_models(test_config) -> list[ModelConfig]:
    return [
        ModelConfig(**cfg) for cfg in test_config.get("judge_models", [])
    ]


def pytest_generate_tests(metafunc):
    """Parametrize tests over discovered rubrics and their scenarios."""
    if "rubric_scenario" in metafunc.fixturenames:
        rubrics = discover_rubrics()
        cases = []
        ids = []
        for rubric in rubrics:
            skill_name = rubric.get("skill", "unknown")
            persona = rubric.get("persona", "unknown")
            version = rubric.get("_version", "0.0.0")
            system_prompt = load_skill_as_system_prompt(rubric["_skill_path"])
            for scenario in rubric.get("test_scenarios", []):
                cases.append({
                    "rubric": rubric,
                    "scenario": scenario,
                    "system_prompt": system_prompt,
                    "skill_name": skill_name,
                    "persona": persona,
                    "version": version,
                })
                ids.append(f"{skill_name}::{scenario['id']}")
        metafunc.parametrize("rubric_scenario", cases, ids=ids)
