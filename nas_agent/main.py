# main.py

from config.settings import APP_NAME, APP_VERSION, MODEL_NAME
from runtime.memory_store import MemoryStore
from runtime.chat_engine import check_model_exists, stream_chat
from gateway.command_parser import try_handle_local_query, print_help
from tools.loader import load_tools_from_manifests


def main():
    print(f"🚀 {APP_NAME} 启动中...")
    print(f"📦 当前版本: {APP_VERSION}")
    print(f"🤖 当前模型: {MODEL_NAME}")
    print("💡 输入 /help 查看命令，输入 /exit 退出")
    print("-" * 60)

    if check_model_exists():
        print(f"✅ 已检测到模型: {MODEL_NAME}")
    else:
        print(f"⚠️ 未确认到模型: {MODEL_NAME}")

    memory = MemoryStore()
    registry = load_tools_from_manifests()

    while True:
        try:
            user_input = input("\n🧑 管理员 (你): ").strip()

            if not user_input:
                continue

            if user_input.lower() in ["/exit", "exit", "quit", "退出"]:
                print("👋 Agent 已关闭。")
                break

            if user_input == "/reset":
                memory.reset()
                print("🧹 当前会话记忆已清空。")
                continue

            if user_input == "/history":
                print(f"🧠 当前缓存消息数: {memory.history_count()}")
                continue

            if user_input == "/help":
                print_help(registry)
                continue

            if try_handle_local_query(user_input, registry):
                continue

            memory.add_user(user_input)
            ai_reply = stream_chat(memory.get_messages())

            if ai_reply:
                memory.add_assistant(ai_reply)
            else:
                print("⚠️ 本次返回为空，可能是模型生成异常。")

        except KeyboardInterrupt:
            print("\n\n👋 收到中断指令，Agent 已关闭。")
            break

        except Exception as e:
            print(f"\n❌ 运行失败: {e}")


if __name__ == "__main__":
    main()