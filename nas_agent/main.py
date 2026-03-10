from __future__ import annotations

from config.settings import MODEL_NAME
from gateway.command_parser import try_handle_local_query
from runtime.agent_loop import run_agent_with_tools
from runtime.memory_store import MemoryStore
from tools.loader import load_tools_from_manifests


def _safe_tool_count(registry) -> int:
    if hasattr(registry, "list_tools"):
        try:
            return len(registry.list_tools())
        except Exception:
            pass

    if hasattr(registry, "tools"):
        tools_obj = registry.tools
        if isinstance(tools_obj, dict):
            return len(tools_obj)
        if isinstance(tools_obj, list):
            return len(tools_obj)

    return 0


def main():
    print(f"✅ 已检测到模型: {MODEL_NAME}")

    registry = load_tools_from_manifests()
    tool_count = _safe_tool_count(registry)

    print(f"🧰 已加载工具数量: {tool_count}")
    print("💡 输入 /help 查看命令，输入 /exit 退出。")

    memory = MemoryStore()

    while True:
        try:
            user_input = input("\n🧑 管理员 (你): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n已退出。")
            break

        if not user_input:
            continue

        if user_input.lower() in {"exit", "quit", "/exit", "/quit"}:
            print("已退出。")
            break

        # 只处理显式命令，例如 /help /search ...
        if try_handle_local_query(user_input, registry):
            continue

        # 普通自然语言进入 Agent 流程
        memory.add_user(user_input)

        try:
            ai_reply = run_agent_with_tools(
                user_input=user_input,
                registry=registry,
                history=memory.get_messages()
            )
        except Exception as e:
            print(f"\n❌ Agent 执行失败: {e}")
            continue

        if ai_reply:
            print(f"\n🤖 本地 Agent: {ai_reply}")
            memory.add_assistant(ai_reply)
        else:
            print("\n⚠️ 本次返回为空，可能是模型生成异常。")


if __name__ == "__main__":
    main()