# tools/system/status/formatter.py

from utils.helpers import seconds_to_human


def print_result(result: dict):
    if not result.get("ok"):
        print(f"❌ 系统状态获取失败: {result.get('error', '未知错误')}")
        return

    data = result["data"]

    print("\n🖥️ 系统状态")
    print(f"   系统: {data.get('system', '未知')} {data.get('release', '')}")
    print(f"   版本: {data.get('version', '未知')}")
    print(f"   架构: {data.get('machine', '未知')}")
    print(f"   主机名: {data.get('hostname', '未知')}")
    print(f"   处理器: {data.get('processor', '未知')}")
    print(f"   Python: {data.get('python_version', '未知')}")
    print(f"   运行时长: {seconds_to_human(data.get('uptime_seconds', 0))}")

    cpu = data.get("cpu", {})
    if "error" not in cpu:
        print(f"   CPU 占用: {cpu.get('usage_percent', '未知')}%")
        print(
            f"   CPU 核心: {cpu.get('physical_cores', '未知')} 物理 / "
            f"{cpu.get('logical_cores', '未知')} 逻辑"
        )
        if cpu.get("current_freq_mhz") is not None:
            print(f"   CPU 当前频率: {cpu.get('current_freq_mhz')} MHz")

    memory = data.get("memory", {})
    if "error" not in memory:
        print(f"   内存占用: {memory.get('usage_percent', '未知')}%")
        print(
            f"   内存已用: {memory.get('used', '未知')} / "
            f"{memory.get('total', '未知')}"
        )
        print(
            f"   交换分区: {memory.get('swap_used', '未知')} / "
            f"{memory.get('swap_total', '未知')} "
            f"({memory.get('swap_usage_percent', '未知')}%)"
        )

    gpu = data.get("gpu", {})
    if gpu.get("detected"):
        print(f"   GPU 数量: {gpu.get('count', 0)}")
        for i, item in enumerate(gpu.get("gpus", []), start=1):
            print(
                f"   GPU#{i}: {item.get('name', '未知')} | "
                f"利用率 {item.get('utilization_gpu_percent', '未知')}% | "
                f"显存 {item.get('memory_used_mb', '未知')}/"
                f"{item.get('memory_total_mb', '未知')} MB | "
                f"温度 {item.get('temperature_c', '未知')}°C"
            )
    else:
        print(f"   GPU: {gpu.get('message', '未检测到')}")

    disk = data.get("disk", {})
    if "error" not in disk:
        print("   磁盘:")
        for part in disk.get("partitions", [])[:10]:
            if "error" in part:
                print(f"      {part.get('mountpoint', '未知')}: {part['error']}")
            else:
                print(
                    f"      {part.get('mountpoint', '未知')}: "
                    f"{part.get('used', '未知')} / {part.get('total', '未知')} "
                    f"({part.get('usage_percent', '未知')}%)"
                )