# tools/loader.py

import importlib
from pathlib import Path
from typing import Any

from tools.base import Tool
from tools.registry import ToolRegistry


TOOLS_ROOT = Path(__file__).resolve().parent


def _parse_value(value: str) -> Any:
    value = value.strip()

    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False

    if value.startswith("[") and value.endswith("]"):
        raw = value[1:-1].strip()
        if not raw:
            return []
        return [x.strip().strip('"').strip("'") for x in raw.split(",")]

    return value.strip('"').strip("'")


def load_tool_manifest(md_path: Path) -> dict:
    text = md_path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise ValueError(f"{md_path} 缺少 frontmatter")

    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"{md_path} frontmatter 格式错误")

    frontmatter = parts[1]
    data = {}

    for line in frontmatter.splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = _parse_value(value)

    return data


def import_callable(callable_path: str):
    module_path, func_name = callable_path.split(":")
    module = importlib.import_module(module_path)
    return getattr(module, func_name)


def load_tools_from_manifests() -> ToolRegistry:
    registry = ToolRegistry()

    for md_path in TOOLS_ROOT.rglob("TOOL.md"):
        manifest = load_tool_manifest(md_path)

        handler = import_callable(manifest["handler"])
        formatter = None
        if manifest.get("formatter"):
            formatter = import_callable(manifest["formatter"])

        tool = Tool(
            name=manifest["name"],
            description=manifest.get("description", ""),
            handler=handler,
            category=manifest.get("category", "general"),
            command=manifest.get("command", ""),
            aliases=manifest.get("aliases", []),
            keywords=manifest.get("keywords", []),
            show_in_help=manifest.get("show_in_help", True),
            formatter=formatter,
            arg_mode=manifest.get("arg_mode", "none"),
        )
        registry.register(tool)

    return registry