def print_result(result: dict):
    if not result.get("ok"):
        print(f"❌ 联网搜索失败: {result.get('error', '未知错误')}")
        return

    print("\n🌐 百度联网搜索")
    print(f"🔎 查询: {result.get('query', '')}\n")

    answer = (result.get("answer") or "").strip()
    if answer:
        print(answer)
    else:
        print("⚠️ 已调用成功，但没有可展示的摘要内容。")