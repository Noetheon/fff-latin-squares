#!/usr/bin/env python3
"""Inventory local SAT/CP solver availability for the Weg-B FFF run."""

from __future__ import annotations

import argparse
import importlib
import json
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Any


PYTHON_MODULES = [
    ("ortools", "ortools"),
    ("z3", "z3"),
    ("pysat / python-sat", "pysat"),
    ("pycosat", "pycosat"),
]

CLI_TOOLS = ["kissat", "cadical", "glucose", "minisat", "sage", "gap"]


def module_inventory(label: str, module_name: str) -> dict[str, Any]:
    result: dict[str, Any] = {
        "label": label,
        "module": module_name,
        "available": False,
        "version": None,
        "error": None,
    }
    try:
        module = importlib.import_module(module_name)
        result["available"] = True
        result["version"] = getattr(module, "__version__", None)
    except Exception as exc:  # noqa: BLE001 - inventory should record any import failure.
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def cli_version(path: str) -> str | None:
    commands = ([path, "--version"], [path, "-version"], [path, "-h"])
    for command in commands:
        try:
            proc = subprocess.run(command, text=True, capture_output=True, timeout=5, check=False)
        except Exception:
            continue
        text = (proc.stdout or proc.stderr).strip().splitlines()
        if text:
            return text[0][:300]
    return None


def cli_inventory(name: str) -> dict[str, Any]:
    path = shutil.which(name)
    return {
        "name": name,
        "available": path is not None,
        "path": path,
        "version_probe": cli_version(path) if path else None,
    }


def make_summary(result: dict[str, Any]) -> str:
    lines = [
        "Solver inventory summary",
        "",
        f"Python: {result['environment']['python']}",
        f"Platform: {result['environment']['platform']}",
        "",
        "Python modules:",
    ]
    for item in result["python_modules"]:
        version = item["version"] if item["version"] is not None else "unknown"
        if item["available"]:
            lines.append(f"- {item['label']}: available, version={version}")
        else:
            lines.append(f"- {item['label']}: missing ({item['error']})")
    lines.extend(["", "CLI tools:"])
    for item in result["cli_tools"]:
        if item["available"]:
            lines.append(f"- {item['name']}: available at {item['path']}; probe={item['version_probe']}")
        else:
            lines.append(f"- {item['name']}: missing")
    lines.extend(
        [
            "",
            f"Strong solver available: {result['summary']['strong_solver_available']}",
            f"Available strong solvers: {result['summary']['available_strong_solvers']}",
        ]
    )
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    py_items = [module_inventory(label, module) for label, module in PYTHON_MODULES]
    cli_items = [cli_inventory(name) for name in CLI_TOOLS]
    strong = []
    for item in py_items:
        if item["available"]:
            strong.append(item["label"])
    for item in cli_items:
        if item["available"] and item["name"] in {"kissat", "cadical", "glucose", "minisat"}:
            strong.append(item["name"])
    result = {
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
        },
        "python_modules": py_items,
        "cli_tools": cli_items,
        "summary": {
            "strong_solver_available": bool(strong),
            "available_strong_solvers": strong,
            "policy": "No n=10/n=12 SAT or UNSAT claim is made without a usable solver run.",
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    args.summary.write_text(make_summary(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
