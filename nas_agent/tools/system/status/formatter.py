def _fmt_uptime(seconds: float) -> str:
    seconds = int(seconds or 0)
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60

    parts = []
    if days:
        parts.append(f"{days}天")
    if hours:
        parts.append(f"{hours}小时")
    if minutes or not parts:
        parts.append(f"{minutes}分钟")
    return "".join(parts)


def print_result(result: dict):
    if not result.get("ok"):
        print(f"❌ 获取系统信息失败: {result.get('error', '未知错误')}")
        return

    data = result.get("data", {}) or {}

    system = data.get("system", "未知系统")
    release = data.get("release", "")
    version = data.get("version", "")
    hostname = data.get("hostname", "未知主机")
    uptime = _fmt_uptime(data.get("uptime_seconds", 0))

    cpu = data.get("cpu", {}) or {}
    memory = data.get("memory", {}) or {}
    disk = data.get("disk", {}) or {}
    gpu = data.get("gpu", {}) or {}

    print("\n🖥️ 系统状态概览\n")
    print(f"主机名：{hostname}")
    print(f"系统：{system} {release} {version}".strip())
    print(f"已运行：{uptime}")

    cpu_usage = cpu.get("usage_percent")
    physical_cores = cpu.get("physical_cores")
    logical_cores = cpu.get("logical_cores")
    current_freq = cpu.get("current_freq_mhz")

    if cpu_usage is not None:
        print(f"\nCPU 当前占用：{cpu_usage}%")
        print(f"CPU 核心：物理 {physical_cores} 核 / 逻辑 {logical_cores} 线程")
        if current_freq:
            print(f"当前频率：{current_freq} MHz")

    mem_total = memory.get("total")
    mem_used = memory.get("used")
    mem_available = memory.get("available")
    mem_usage = memory.get("usage_percent")

    if mem_total:
        print(f"\n内存使用：{mem_used} / {mem_total}（{mem_usage}%）")
        print(f"可用内存：{mem_available}")

    partitions = disk.get("partitions", []) or []
    if partitions:
        print("\n磁盘情况：")
        for part in partitions[:6]:
            mountpoint = part.get("mountpoint", "")
            used = part.get("used", "")
            total = part.get("total", "")
            usage_percent = part.get("usage_percent", "")
            free = part.get("free", "")
            print(f"- {mountpoint}：已用 {used} / {total}（{usage_percent}%），剩余 {free}")

    if gpu.get("detected"):
        gpus = gpu.get("gpus", []) or []
        if gpus:
            first_gpu = gpus[0]
            print("\n显卡状态：")
            print(f"- 型号：{first_gpu.get('name', '未知')}")
            print(f"- 温度：{first_gpu.get('temperature_c', 'N/A')}°C")
            print(f"- 占用：{first_gpu.get('utilization_gpu_percent', 'N/A')}%")
            print(
                f"- 显存：{first_gpu.get('memory_used_mb', 'N/A')} MB / "
                f"{first_gpu.get('memory_total_mb', 'N/A')} MB"
            )
            print(
                f"- 功耗：{first_gpu.get('power_draw_w', 'N/A')} W / "
                f"{first_gpu.get('power_limit_w', 'N/A')} W"
            )

    print("\n整体来看，系统目前运行正常，资源状态已经帮你整理好了。")