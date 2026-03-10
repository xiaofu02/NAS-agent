# tools/system/status/tool.py

import platform
import shutil
import subprocess
import time

from utils.deps import ensure_package
from utils.helpers import bytes_to_human

psutil = ensure_package("psutil")


def _get_cpu_info() -> dict:
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_per_core = psutil.cpu_percent(interval=1, percpu=True)
        freq = psutil.cpu_freq()

        return {
            "usage_percent": cpu_percent,
            "physical_cores": psutil.cpu_count(logical=False),
            "logical_cores": psutil.cpu_count(logical=True),
            "per_core_percent": cpu_per_core,
            "current_freq_mhz": round(freq.current, 2) if freq else None,
            "min_freq_mhz": round(freq.min, 2) if freq else None,
            "max_freq_mhz": round(freq.max, 2) if freq else None,
        }
    except Exception as e:
        return {"error": str(e)}


def _get_memory_info() -> dict:
    try:
        vm = psutil.virtual_memory()
        sm = psutil.swap_memory()

        return {
            "total_bytes": vm.total,
            "available_bytes": vm.available,
            "used_bytes": vm.used,
            "usage_percent": vm.percent,
            "total": bytes_to_human(vm.total),
            "available": bytes_to_human(vm.available),
            "used": bytes_to_human(vm.used),
            "swap_total_bytes": sm.total,
            "swap_used_bytes": sm.used,
            "swap_free_bytes": sm.free,
            "swap_usage_percent": sm.percent,
            "swap_total": bytes_to_human(sm.total),
            "swap_used": bytes_to_human(sm.used),
            "swap_free": bytes_to_human(sm.free),
        }
    except Exception as e:
        return {"error": str(e)}


def _get_disk_info() -> dict:
    try:
        partitions_info = []

        for part in psutil.disk_partitions(all=False):
            try:
                usage = psutil.disk_usage(part.mountpoint)
                partitions_info.append({
                    "device": part.device,
                    "mountpoint": part.mountpoint,
                    "fstype": part.fstype,
                    "opts": getattr(part, "opts", ""),
                    "total_bytes": usage.total,
                    "used_bytes": usage.used,
                    "free_bytes": usage.free,
                    "usage_percent": usage.percent,
                    "total": bytes_to_human(usage.total),
                    "used": bytes_to_human(usage.used),
                    "free": bytes_to_human(usage.free),
                })
            except PermissionError:
                partitions_info.append({
                    "device": part.device,
                    "mountpoint": part.mountpoint,
                    "fstype": part.fstype,
                    "error": "权限不足，无法读取"
                })
            except Exception as e:
                partitions_info.append({
                    "device": part.device,
                    "mountpoint": part.mountpoint,
                    "fstype": part.fstype,
                    "error": str(e)
                })

        io = psutil.disk_io_counters()
        io_data = None
        if io:
            io_data = {
                "read_count": io.read_count,
                "write_count": io.write_count,
                "read_bytes_raw": io.read_bytes,
                "write_bytes_raw": io.write_bytes,
                "read_bytes": bytes_to_human(io.read_bytes),
                "write_bytes": bytes_to_human(io.write_bytes),
                "read_time_ms": getattr(io, "read_time", None),
                "write_time_ms": getattr(io, "write_time", None),
            }

        return {
            "partitions": partitions_info,
            "io": io_data
        }
    except Exception as e:
        return {"error": str(e)}


def _get_gpu_info() -> dict:
    try:
        if not shutil.which("nvidia-smi"):
            return {
                "detected": False,
                "message": "未检测到 nvidia-smi，可能没有 NVIDIA GPU，或未安装驱动。"
            }

        cmd = [
            "nvidia-smi",
            "--query-gpu=name,temperature.gpu,utilization.gpu,memory.total,memory.used,memory.free,power.draw,power.limit",
            "--format=csv,noheader,nounits"
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=10
        )

        if result.returncode != 0:
            return {
                "detected": False,
                "message": result.stderr.strip() or "nvidia-smi 执行失败"
            }

        gpus = []
        lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]

        for line in lines:
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 8:
                gpus.append({
                    "name": parts[0],
                    "temperature_c": parts[1],
                    "utilization_gpu_percent": parts[2],
                    "memory_total_mb": parts[3],
                    "memory_used_mb": parts[4],
                    "memory_free_mb": parts[5],
                    "power_draw_w": parts[6],
                    "power_limit_w": parts[7],
                })

        return {
            "detected": True,
            "count": len(gpus),
            "gpus": gpus
        }

    except subprocess.TimeoutExpired:
        return {"detected": False, "message": "nvidia-smi 执行超时"}
    except Exception as e:
        return {"detected": False, "message": str(e)}


def get_system_status() -> dict:
    try:
        return {
            "ok": True,
            "name": "system_status",
            "data": {
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "hostname": platform.node(),
                "python_version": platform.python_version(),
                "uptime_seconds": round(time.time() - psutil.boot_time(), 2),
                "cpu": _get_cpu_info(),
                "memory": _get_memory_info(),
                "disk": _get_disk_info(),
                "gpu": _get_gpu_info(),
            }
        }
    except Exception as e:
        return {
            "ok": False,
            "name": "system_status",
            "error": str(e)
        }