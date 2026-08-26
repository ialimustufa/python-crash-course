"""Minimal notebook writer used by generate_notebooks.py."""

from __future__ import annotations

import json
from pathlib import Path


METADATA = {
    "kernelspec": {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3",
    },
    "language_info": {
        "name": "python",
        "pygments_lexer": "ipython3",
        "version": "3.11.0",
    },
    "colab": {"provenance": [], "toc_visible": True},
}


def _src(text: str) -> list[str]:
    text = text.strip("\n") + "\n"
    return [text]


def markdown_cell(text: str, cell_id: str) -> dict:
    return {
        "cell_type": "markdown",
        "id": cell_id,
        "metadata": {},
        "source": _src(text),
    }


def code_cell(text: str, cell_id: str) -> dict:
    return {
        "cell_type": "code",
        "id": cell_id,
        "metadata": {},
        "source": _src(text),
        "outputs": [],
        "execution_count": None,
    }


def write_notebook(path: Path, cells: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    notebook = {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": METADATA,
        "cells": cells,
    }
    path.write_text(json.dumps(notebook, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
