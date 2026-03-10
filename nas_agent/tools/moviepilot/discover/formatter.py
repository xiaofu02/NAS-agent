# tools/moviepilot/discover/formatter.py

def print_result(result: dict):
    if not result.get("ok"):
        print("\n❌ MoviePilot 接口发现失败")
        print(f"   错误: {result.get('error', '未知错误')}")
        data = result.get("data", {})
        if data:
            print(f"   地址: {data.get('base_url', '未知')}")
        return

    data = result["data"]

    print("\n🧭 MoviePilot 接口发现")
    print(f"   地址: {data.get('base_url', '未知')}")
    print(f"   Docs: {data.get('docs_url', '未知')}")
    print(f"   脚本数量: {data.get('script_count', 0)}")
    print(f"   发现路径数: {data.get('path_count', 0)}")

    fetched = data.get("fetched_scripts", [])
    if fetched:
        ok_count = sum(1 for item in fetched if item.get("ok"))
        print(f"   成功抓取脚本: {ok_count}/{len(fetched)}")

    paths = data.get("paths", [])
    if not paths:
        print("   未从前端资源中提取到 /api/... 路径")
        return

    print("   接口线索:")
    for path in paths[:80]:
        print(f"      {path}")

    if len(paths) > 80:
        print(f"      ... 其余 {len(paths) - 80} 条未显示")