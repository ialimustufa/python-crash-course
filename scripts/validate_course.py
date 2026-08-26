#!/usr/bin/env python3
"""Validate maintained course notebooks, dashboard manifest, and optional execution."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_DIR = ROOT / "notebooks"
SITE_DIR = ROOT / "site"
COURSE_JSON = SITE_DIR / "course.json"
README = ROOT / "README.md"

PRACTICE_RE = re.compile(r"Practice (\d{2}\.\d+)")
HINT_RE = re.compile(r"Hint (\d{2}\.\d+)")
SOLUTION_RE = re.compile(r"Solution (\d{2}\.\d+)")
CHECK_RE = re.compile(r"Check (\d{2}\.\d+)|Practice (\d{2}\.\d+) passed")
COLAB_RE = re.compile(
    r"https://colab\.research\.google\.com/github/ialimustufa/python-crash-course/blob/master/notebooks/([A-Za-z0-9_.-]+\.ipynb)"
)


def cell_text(cell: dict) -> str:
    source = cell.get("source", [])
    if isinstance(source, str):
        return source
    return "".join(source)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def notebook_paths() -> list[Path]:
    return sorted(NOTEBOOK_DIR.glob("*.ipynb"))


def fail(messages: list[str]) -> None:
    if messages:
        print("\n".join(messages))
        raise SystemExit(1)


def check_structure() -> None:
    errors: list[str] = []
    notebooks = notebook_paths()
    if len(notebooks) != 8:
        errors.append(f"expected 8 notebooks in notebooks/, found {len(notebooks)}")

    course = load_json(COURSE_JSON)
    lesson_files = [item["file"] for item in course["lessons"]]
    if len(course["lessons"]) != 8:
        errors.append("site/course.json must list 8 lessons")

    for index, path in enumerate(notebooks):
        nb = load_json(path)
        if nb.get("nbformat") != 4:
            errors.append(f"{path.name}: nbformat must be 4")
        cells = nb.get("cells", [])
        if not cells:
            errors.append(f"{path.name}: has no cells")
            continue
        text = "\n".join(cell_text(cell) for cell in cells)
        match = COLAB_RE.search(text)
        if not match or match.group(1) != path.name:
            errors.append(f"{path.name}: missing or mismatched Colab badge")
        if "How to use this notebook" not in text:
            errors.append(f"{path.name}: missing usage section")
        if "## Navigation" not in text:
            errors.append(f"{path.name}: missing navigation")
        practices = set(PRACTICE_RE.findall(text))
        hints = set(HINT_RE.findall(text))
        solutions = set(SOLUTION_RE.findall(text))
        checks = set()
        for found in CHECK_RE.findall(text):
            checks.add(found[0] or found[1])
        if not practices:
            errors.append(f"{path.name}: no Practice IDs found")
        missing_hints = practices - hints
        missing_solutions = practices - solutions
        missing_checks = practices - checks
        if missing_hints:
            errors.append(f"{path.name}: missing hints for {sorted(missing_hints)}")
        if missing_solutions:
            errors.append(f"{path.name}: missing solutions for {sorted(missing_solutions)}")
        if missing_checks:
            errors.append(f"{path.name}: missing checks for {sorted(missing_checks)}")
        expected = f"notebooks/{path.name}"
        if expected not in lesson_files:
            errors.append(f"{path.name}: not listed in site/course.json")
        lesson = course["lessons"][index] if index < len(course["lessons"]) else None
        if lesson and lesson["file"] != expected:
            errors.append(f"course.json lesson {index} file mismatch: {lesson['file']} vs {expected}")
        for lesson in course["lessons"]:
            if lesson["file"] == expected:
                if len(lesson.get("quiz", [])) < 1:
                    errors.append(f"{path.name}: course.json quiz missing")
                if len(lesson.get("milestones", [])) < 1:
                    errors.append(f"{path.name}: course.json milestones missing")

    readme = README.read_text(encoding="utf-8")
    for path in notebooks:
        if path.name not in readme:
            errors.append(f"README.md does not mention {path.name}")
    if "fork" not in readme.lower():
        errors.append("README.md should explain how to fork the course")
    if "github.io" not in readme.lower() and "GitHub Pages" not in readme:
        errors.append("README.md should mention GitHub Pages")
    if "legacy/" not in readme:
        errors.append("README.md should link the legacy archive")

    required_site = [
        SITE_DIR / "index.html",
        SITE_DIR / "course.json",
        SITE_DIR / "config.json",
        SITE_DIR / "assets" / "app.js",
        SITE_DIR / "assets" / "styles.css",
    ]
    for path in required_site:
        if not path.exists():
            errors.append(f"missing {path.relative_to(ROOT)}")

    fail(errors)
    print("structure checks passed")


def execute_notebook(path: Path, output: Path | None = None) -> None:
    import nbformat
    from nbclient import NotebookClient

    path = path.resolve()
    nb = nbformat.read(path, as_version=4)
    client = NotebookClient(
        nb,
        timeout=180,
        kernel_name="python3",
        allow_errors=False,
        resources={"metadata": {"path": str(path.parent)}},
    )
    try:
        client.execute()
    except Exception:
        if output:
            output = output.resolve()
            output.parent.mkdir(parents=True, exist_ok=True)
            nbformat.write(nb, output)
        raise
    print(f"executed {path.relative_to(ROOT)}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--structure", action="store_true")
    parser.add_argument("--execute", type=Path)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--artifact-dir", type=Path, default=ROOT / "artifacts")
    args = parser.parse_args()

    os.chdir(ROOT)
    if args.structure or args.all:
        check_structure()
    if args.execute:
        artifact = args.artifact_dir / args.execute.name
        execute_notebook(args.execute, artifact)
    elif args.all:
        for path in notebook_paths():
            execute_notebook(path, args.artifact_dir / path.name)


if __name__ == "__main__":
    main()
