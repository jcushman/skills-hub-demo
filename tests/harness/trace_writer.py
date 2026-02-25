"""Write conversation traces and evaluation reports to disk.

Traces are saved as JSON files under a top-level traces/ directory that mirrors
the skills/ structure:

    traces/<persona>/<skill-name>/<version>/<scenario-id>_<sequence>.json

The sequence number auto-increments so multiple runs of the same scenario
accumulate over time, enabling quality trending.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from .evaluator import EvaluationReport
from .runner import ConversationTrace, ModelConfig

log = logging.getLogger("harness.traces")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
TRACES_DIR = PROJECT_ROOT / "traces"


def _next_sequence(directory: Path, prefix: str) -> int:
    """Find the next available sequence number for a given scenario prefix."""
    existing = sorted(directory.glob(f"{prefix}_*.json"))
    if not existing:
        return 1
    last = existing[-1].stem
    try:
        return int(last.rsplit("_", 1)[1]) + 1
    except (IndexError, ValueError):
        return len(existing) + 1


def save_trace(
    trace: ConversationTrace,
    report: EvaluationReport,
    *,
    persona: str,
    version: str,
    scenario: dict,
    model_config: ModelConfig,
    judge_config: ModelConfig,
) -> Path:
    """Serialize a trace + evaluation to JSON and write it to traces/.

    Returns the path to the written file.
    """
    out_dir = TRACES_DIR / persona / trace.skill_name / version
    out_dir.mkdir(parents=True, exist_ok=True)

    seq = _next_sequence(out_dir, trace.scenario_id)
    filename = f"{trace.scenario_id}_{seq:04d}.json"
    out_path = out_dir / filename

    record = {
        "meta": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "persona": persona,
            "skill": trace.skill_name,
            "version": version,
            "scenario_id": trace.scenario_id,
        },
        "config": {
            "model_under_test": asdict(model_config),
            "judge_model": asdict(judge_config),
        },
        "scenario": {
            "id": scenario["id"],
            "setup": scenario.get("setup", ""),
            "messages": scenario.get("messages", []),
            "expected": scenario.get("expected", []),
        },
        "conversation": [
            {"role": m.role, "content": m.content}
            for m in trace.messages
        ],
        "evaluation": {
            "score": round(report.score(), 1),
            "structural": [asdict(c) for c in report.structural],
            "pedagogical": [asdict(c) for c in report.pedagogical],
            "anti_patterns": [asdict(c) for c in report.anti_patterns],
        },
    }

    out_path.write_text(
        json.dumps(record, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    rel_project = out_path.relative_to(PROJECT_ROOT)
    log.info("Trace saved: %s", rel_project)
    return out_path


def trace_exists(skill: str, version: str, scenario_id: str, model: str) -> bool:
    """Check whether a trace already exists on disk for this combination.

    Scans trace files directly rather than relying on index.json, which may
    be stale (it's only rebuilt at session end and won't exist if a previous
    run was interrupted).
    """
    for trace_file in TRACES_DIR.glob(f"*/{skill}/{version}/{scenario_id}_*.json"):
        try:
            record = json.loads(trace_file.read_text(encoding="utf-8"))
            if record["config"]["model_under_test"]["model"] == model:
                return True
        except (json.JSONDecodeError, KeyError, OSError):
            continue
    return False


def rebuild_index() -> int:
    """Rebuild traces/index.json from all trace files on disk.

    Returns the number of traces indexed.  Safe to call after parallel test
    runs since it reads finished files rather than maintaining incremental state.
    """
    entries = []
    for trace_file in sorted(TRACES_DIR.rglob("*.json")):
        if trace_file.name == "index.json":
            continue
        try:
            record = json.loads(trace_file.read_text(encoding="utf-8"))
            meta = record["meta"]
            config = record["config"]
            rel_path = trace_file.relative_to(TRACES_DIR)
            entries.append({
                "path": str(rel_path),
                "persona": meta["persona"],
                "skill": meta["skill"],
                "version": meta["version"],
                "scenario_id": meta["scenario_id"],
                "timestamp": meta["timestamp"],
                "score": record["evaluation"]["score"],
                "model": config["model_under_test"]["model"],
                "judge": config["judge_model"]["model"],
            })
        except (json.JSONDecodeError, KeyError) as exc:
            log.warning("Skipping malformed trace %s: %s", trace_file, exc)

    entries.sort(key=lambda e: e["timestamp"])
    index_path = TRACES_DIR / "index.json"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(
        json.dumps({"traces": entries}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    log.info("Rebuilt trace index: %d traces", len(entries))
    return len(entries)
