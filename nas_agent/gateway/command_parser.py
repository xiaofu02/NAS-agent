# gateway/command_parser.py

from tools.registry import ToolRegistry
from utils.formatters import print_generic_json


def print_help(registry: ToolRegistry):
    print("\n可用命令：")
    grouped = registry.list_by_category()

    for category, tools in grouped.items():
        print(f"\n[{category}]")
        for tool in tools:
            if tool.show_in_help:
                print(f"  {tool.command:<14} {tool.description}")


def print_tool_result(tool, result: dict):
    if tool.formatter:
        tool.formatter(result)
    else:
        print_generic_json(result)


def _run_command_tool(text: str, registry: ToolRegistry) -> bool:
    parts = text.split(maxsplit=1)
    command = parts[0]
    tail = parts[1].strip() if len(parts) > 1 else ""

    tool = registry.get_by_command(command)
    if not tool:
        return False

    if tool.arg_mode == "text_tail":
        result = registry.run(tool.name, tail)
    else:
        result = registry.run(tool.name)

    print_tool_result(tool, result)
    return True


def try_handle_local_query(user_input: str, registry: ToolRegistry) -> bool:
    text = user_input.strip()

    if text == "/help":
        print_help(registry)
        return True

    if text.startswith("/"):
        return _run_command_tool(text, registry)

    matched_tool = registry.match_by_text(text)
    if matched_tool:
        result = registry.run(matched_tool.name)
        print_tool_result(matched_tool, result)
        return True

    return False