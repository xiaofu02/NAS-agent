from __future__ import annotations

from tools.registry import ToolRegistry


def print_help(registry: ToolRegistry) -> None:
    print("\n📘 可用命令：")
    tools = []

    if hasattr(registry, "list_tools"):
        tools = registry.list_tools()
    elif hasattr(registry, "tools"):
        tools_obj = registry.tools
        if isinstance(tools_obj, dict):
            tools = list(tools_obj.values())
        elif isinstance(tools_obj, list):
            tools = tools_obj

    shown = False
    for tool in tools:
        show_in_help = getattr(tool, "show_in_help", True)
        if not show_in_help:
            continue

        command = getattr(tool, "command", "")
        description = getattr(tool, "description", "")
        aliases = getattr(tool, "aliases", []) or []

        alias_text = ""
        if aliases:
            alias_text = f" (别名: {', '.join(str(x) for x in aliases)})"

        print(f"  {command} - {description}{alias_text}")
        shown = True

    if not shown:
        print("  暂无可用命令")

    print("  /help - 显示帮助")
    print("  /exit - 退出程序")


def print_tool_result(tool, result) -> None:
    formatter = getattr(tool, "formatter", None)

    if formatter:
        try:
            formatter(result)
            return
        except Exception as e:
            print(f"⚠️ 工具格式化输出失败: {e}")
            print(result)
            return

    print(result)


def _run_command_tool(text: str, registry: ToolRegistry) -> bool:
    parts = text.split(maxsplit=1)
    command = parts[0]
    arg_text = parts[1].strip() if len(parts) > 1 else ""

    tool = None

    if hasattr(registry, "get_by_command"):
        tool = registry.get_by_command(command)
    elif hasattr(registry, "find_by_command"):
        tool = registry.find_by_command(command)

    if not tool:
        print(f"❌ 未找到命令: {command}")
        return True

    try:
        arg_mode = getattr(tool, "arg_mode", "")

        if arg_mode == "text_tail":
            result = registry.run(tool.name, arg_text)
        else:
            result = registry.run(tool.name)

        print_tool_result(tool, result)
        return True

    except Exception as e:
        print(f"❌ 执行命令失败: {e}")
        return True


def try_handle_local_query(user_input: str, registry: ToolRegistry) -> bool:
    text = user_input.strip()

    if text == "/help":
        print_help(registry)
        return True

    if text in {"/exit", "/quit"}:
        return False

    if text.startswith("/"):
        return _run_command_tool(text, registry)

    # 关键改动：
    # 普通自然语言不再在这里直接做关键词匹配工具，
    # 而是交给上层的本地 AI 决定是否调用工具。
    return False