# tools/moviepilot/get/formatter.py

import json


def print_result(result: dict):
    if not result.get("ok"):
        print("\n❌ MoviePilot GET 失败")
        print(f"   错误: {result.get('error', '未知错误')}")
        data = result.get("data", {})
        if data:
            print(f"   地址: {data.get('base_url', '未知')}")
            print(f"   路径: {data.get('path', '未知')}")
        return

    data = result["data"]

    print("\n🔎 MoviePilot GET")
    print(f"   地址: {data.get('base_url', '未知')}")
    print(f"   路径: {data.get('path', '未知')}")
    print(f"   鉴权方式: {data.get('auth_mode', '未知')}")
    print(f"   状态码: {data.get('status_code', '未知')}")

    if data.get("json") is not None:
        print("   JSON 返回:")
        print(json.dumps(data["json"], indent=2, ensure_ascii=False)[:2500])
    else:
        print("   文本预览:")
        print(data.get("text_preview", ""))