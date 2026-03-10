# tools/registry.py

from typing import Dict, Optional, Any
from tools.base import Tool


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        self._commands: Dict[str, str] = {}

    def register(self, tool: Tool):
        self._tools[tool.name] = tool
        if tool.command:
            self._commands[tool.command] = tool.name

    def get(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def get_by_command(self, command: str) -> Optional[Tool]:
        tool_name = self._commands.get(command)
        if not tool_name:
            return None
        return self._tools.get(tool_name)

    def has(self, name: str) -> bool:
        return name in self._tools

    def run(self, name: str, *args, **kwargs) -> Any:
        tool = self.get(name)
        if not tool:
            raise ValueError(f"工具不存在: {name}")
        return tool.handler(*args, **kwargs)

    def list_tools(self) -> list[Tool]:
        return list(self._tools.values())

    def list_by_category(self) -> dict[str, list[Tool]]:
        grouped: dict[str, list[Tool]] = {}
        for tool in self._tools.values():
            grouped.setdefault(tool.category, []).append(tool)
        return grouped

    def match_by_text(self, text: str) -> Optional[Tool]:
        lowered = text.lower()
        for tool in self._tools.values():
            for kw in tool.keywords:
                if kw.lower() in lowered:
                    return tool
        return None