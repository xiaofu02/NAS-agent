# tools/moviepilot/status/formatter.py

def print_result(result: dict):
    data = result.get("data", {})

    print("\n🎬 MoviePilot 状态")
    print(f"   地址: {data.get('base_url', '未知')}")

    if not result.get("ok"):
        print("   状态: 不可用")

        results = data.get("results", [])
        first_error = None
        for item in results:
            errors = item.get("errors", [])
            if errors:
                first_error = errors[0]
                break

        if first_error:
            print(f"   首个错误: {first_error.get('error', '未知错误')}")
        return

    print("   状态: 在线")

    working_probe = data.get("working_probe")
    if working_probe:
        print("   可用探测:")
        print(f"      接口: {working_probe.get('probe', '未知')}")
        print(f"      路径: {working_probe.get('path', '未知')}")
        print(f"      URL: {working_probe.get('url', '未知')}")
        print(f"      鉴权方式: {working_probe.get('auth_mode', '未知')}")
        print(f"      状态码: {working_probe.get('status_code', '未知')}")
    else:
        print("   当前没有找到可用探测接口")