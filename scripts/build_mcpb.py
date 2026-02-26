#!/usr/bin/env python3
"""Build a Claude Desktop Extension (.mcpb) for the Legal Ed Skills Hub.

Reads templates/mcpb/ (which mirrors the .mcpb zip structure), renders
{{…}} placeholders, and zips the result.

Run after build.py (needs _site/actions/personas.json):

    uv run scripts/build_mcpb.py --base-url https://example.github.io/skills-hub-demo/
"""

import argparse
import json
import os
import tempfile
import zipfile
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MCPB_TEMPLATE_DIR = PROJECT_ROOT / "templates" / "mcpb"
SITE_DIR = PROJECT_ROOT / "_site"


def _build_replacements(base_url: str, site_dir: Path) -> dict[str, str]:
    """Compute all {{…}} replacement values."""
    personas_json_path = site_dir / "actions" / "personas.json"
    personas_data = json.loads(personas_json_path.read_text(encoding="utf-8"))

    lines = []
    for p in personas_data["personas"]:
        lines.append(f"- **{p['id']}**: {p['description']} (objective: {p['objective']})")

    return {
        "base_url": base_url,
        "personas_json": personas_json_path.read_text(encoding="utf-8"),
        "personas_summary": "\n".join(lines),
    }


def _render(text: str, replacements: dict[str, str]) -> str:
    for key, value in replacements.items():
        text = text.replace(f"{{{{{key}}}}}", value)
    return text


def build_mcpb(base_url: str, *, output_dir: Path | None = None, site_dir: Path | None = None):
    """Build the .mcpb file.

    Args:
        base_url: Deployed site base URL.
        output_dir: Where to write the .mcpb. Defaults to _site/.
        site_dir: Location of the built _site/ (for reading actions/personas.json).
    """
    base = base_url if base_url.endswith("/") else base_url + "/"
    if site_dir is None:
        site_dir = SITE_DIR
    if output_dir is None:
        output_dir = SITE_DIR

    replacements = _build_replacements(base, site_dir)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)

        for src in sorted(MCPB_TEMPLATE_DIR.rglob("*")):
            if not src.is_file() or src.name.startswith("."):
                continue
            rel = src.relative_to(MCPB_TEMPLATE_DIR)
            dest = tmp / rel
            dest.parent.mkdir(parents=True, exist_ok=True)

            content = src.read_text(encoding="utf-8")
            if "{{" in content:
                content = _render(content, replacements)
            dest.write_text(content, encoding="utf-8")

        mcpb_path = output_dir / "legal-ed-skills-hub.mcpb"
        mcpb_path.parent.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(mcpb_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for file in sorted(tmp.rglob("*")):
                if not file.is_file():
                    continue
                zf.write(file, file.relative_to(tmp))

        size_kb = mcpb_path.stat().st_size / 1024
        print(f"Built MCPB: {mcpb_path} ({size_kb:.0f} KB)")


def main():
    load_dotenv(PROJECT_ROOT / ".env")

    parser = argparse.ArgumentParser(description="Build Claude Desktop Extension (.mcpb)")
    parser.add_argument(
        "--base-url",
        default=os.environ.get("BASE_URL", ""),
        help="Base URL of the deployed site (required)",
    )
    args = parser.parse_args()

    if not args.base_url:
        parser.error("--base-url is required (or set BASE_URL in .env)")

    build_mcpb(args.base_url)


if __name__ == "__main__":
    main()
