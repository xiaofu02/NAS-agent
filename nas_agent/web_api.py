from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, request
from flask_cors import CORS

from gateway.command_parser import try_handle_local_query
from runtime.agent_loop import run_agent_with_tools
from runtime.memory_store import MemoryStore
from tools.loader import load_tools_from_manifests

CONFIG_PATH = Path(__file__).resolve().parent / "config.runtime.json"
POLL_SECONDS = 3

app = Flask(__name__)
CORS(app)

registry = load_tools_from_manifests()
memory = MemoryStore()
status_cache: dict[str, Any] = {
    "ok": False,
    "host_state": "warning",
    "metrics": {},
    "updated_at": None,
    "error": "尚未完成第一次状态采集",
}


def load_runtime_config() -> dict[str, Any]:
    default_config = {
        "host": "http://127.0.0.1:8080",
        "apiKey": "",
        "baiduKey": "",
        "modelName": os.getenv("MODEL_NAME", "lfm2:24b-a2b"),
        "summaryModel": os.getenv("SUMMARY_MODEL", "lfm2:24b-a2b"),
        "autoSearch": True,
        "darkMode": True,
        "systemPrompt": "你是本地 NAS 智能管家，请自然、简洁地回答问题。",
    }

    if not CONFIG_PATH.exists():
        return default_config

    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            default_config.update(data)
    except Exception:
        pass

    return default_config


def save_runtime_config(data: dict[str, Any]) -> None:
    CONFIG_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _pick_tool_name(candidates: list[str]) -> str | None:
    for name in candidates:
        if hasattr(registry, "has") and registry.has(name):
            return name
        tools = []
        if hasattr(registry, "list_tools"):
            tools = registry.list_tools()
        elif hasattr(registry, "tools"):
            if isinstance(registry.tools, dict):
                tools = list(registry.tools.values())
            elif isinstance(registry.tools, list):
                tools = registry.tools
        for tool in tools:
            if getattr(tool, "name", "") == name:
                return name
    return None


def _run_system_status() -> dict[str, Any]:
    tool_name = _pick_tool_name(["system_status", "system_info", "status", "sys_status"])
    if not tool_name:
        return {"ok": False, "error": "未找到系统状态工具"}

    try:
        try:
            result = registry.run(tool_name, "系统信息")
        except TypeError:
            result = registry.run(tool_name)
        if isinstance(result, dict):
            return result
        return {"ok": False, "error": f"工具返回格式异常: {type(result).__name__}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _host_state_from_data(data: dict[str, Any]) -> str:
    cpu_usage = ((data.get("cpu") or {}).get("usage_percent") or 0)
    mem_usage = ((data.get("memory") or {}).get("usage_percent") or 0)
    disk_parts = (data.get("disk") or {}).get("partitions") or []
    gpu_info = (data.get("gpu") or {}).get("gpus") or []

    disk_max = 0
    for part in disk_parts:
        try:
            disk_max = max(disk_max, float(part.get("usage_percent") or 0))
        except Exception:
            pass

    gpu_usage = 0
    gpu_temp = 0
    if gpu_info:
        g = gpu_info[0]
        try:
            gpu_usage = float(g.get("utilization_gpu_percent") or 0)
        except Exception:
            pass
        try:
            gpu_temp = float(g.get("temperature_c") or 0)
        except Exception:
            pass

    if cpu_usage > 85 or mem_usage > 85 or disk_max > 90 or gpu_usage > 90 or gpu_temp > 82:
        return "critical"
    if cpu_usage > 60 or mem_usage > 70 or disk_max > 80 or gpu_usage > 65 or gpu_temp > 72:
        return "warning"
    return "healthy"


def _compact_metrics(data: dict[str, Any]) -> dict[str, Any]:
    cpu = data.get("cpu") or {}
    memory = data.get("memory") or {}
    disk = data.get("disk") or {}
    gpu = data.get("gpu") or {}
    gpu_list = gpu.get("gpus") or []

    disk_parts = disk.get("partitions") or []
    disk_max = 0
    for part in disk_parts:
        try:
            disk_max = max(disk_max, float(part.get("usage_percent") or 0))
        except Exception:
            pass

    gpu_usage = 0
    gpu_name = None
    gpu_temp = None
    if gpu_list:
        g = gpu_list[0]
        gpu_name = g.get("name")
        try:
            gpu_usage = float(g.get("utilization_gpu_percent") or 0)
        except Exception:
            gpu_usage = 0
        gpu_temp = g.get("temperature_c")

    return {
        "hostname": data.get("hostname"),
        "system": f"{data.get('system', '')} {data.get('release', '')} {data.get('version', '')}".strip(),
        "cpu": float(cpu.get("usage_percent") or 0),
        "memory": float(memory.get("usage_percent") or 0),
        "disk": float(disk_max or 0),
        "gpu": float(gpu_usage or 0),
        "gpuName": gpu_name,
        "gpuTemp": gpu_temp,
        "onlineServices": 12,
        "alerts": 0,
        "raw": data,
    }


def refresh_status_cache() -> None:
    global status_cache
    result = _run_system_status()
    if not result.get("ok"):
        status_cache = {
            "ok": False,
            "host_state": "critical",
            "metrics": {},
            "updated_at": time.time(),
            "error": result.get("error", "状态采集失败"),
        }
        return

    data = result.get("data") or {}
    host_state = _host_state_from_data(data)
    metrics = _compact_metrics(data)
    alerts = 0
    if host_state == "warning":
        alerts = 2
    elif host_state == "critical":
        alerts = 5
    metrics["alerts"] = alerts

    status_cache = {
        "ok": True,
        "host_state": host_state,
        "metrics": metrics,
        "updated_at": time.time(),
        "error": None,
    }


def status_polling_loop() -> None:
    while True:
        try:
            refresh_status_cache()
        except Exception as e:
            status_cache.update(
                {
                    "ok": False,
                    "host_state": "critical",
                    "updated_at": time.time(),
                    "error": str(e),
                }
            )
        time.sleep(POLL_SECONDS)


@app.get("/api/status")
def api_status():
    return jsonify(status_cache)


@app.get("/api/config")
def api_get_config():
    return jsonify({"ok": True, "config": load_runtime_config()})


@app.post("/api/config")
def api_save_config():
    payload = request.get_json(silent=True) or {}
    current = load_runtime_config()
    current.update(payload)
    save_runtime_config(current)
    return jsonify({"ok": True, "config": current})


@app.post("/api/chat")
def api_chat():
    payload = request.get_json(silent=True) or {}
    user_input = str(payload.get("message") or "").strip()
    if not user_input:
        return jsonify({"ok": False, "error": "message 不能为空"}), 400

    if user_input.startswith("/") and try_handle_local_query(user_input, registry):
        return jsonify({
            "ok": True,
            "reply": "命令已在本地执行。",
            "tool_used": True,
        })

    memory.add_user(user_input)
    reply = run_agent_with_tools(
        user_input=user_input,
        registry=registry,
        history=memory.get_messages(),
    )
    if reply:
        memory.add_assistant(reply)

    return jsonify({
        "ok": True,
        "reply": reply or "本地模型没有返回内容。",
        "tool_used": False,
    })


@app.get("/api/tools")
def api_tools():
    tools = []
    if hasattr(registry, "list_tools"):
        source_tools = registry.list_tools()
    elif hasattr(registry, "tools"):
        if isinstance(registry.tools, dict):
            source_tools = list(registry.tools.values())
        else:
            source_tools = registry.tools
    else:
        source_tools = []

    for tool in source_tools:
        tools.append(
            {
                "name": getattr(tool, "name", ""),
                "command": getattr(tool, "command", ""),
                "description": getattr(tool, "description", ""),
                "keywords": getattr(tool, "keywords", []) or [],
                "arg_mode": getattr(tool, "arg_mode", ""),
            }
        )

    return jsonify({"ok": True, "tools": tools})


if __name__ == "__main__":
    threading.Thread(target=status_polling_loop, daemon=True).start()
    refresh_status_cache()
    app.run(host="0.0.0.0", port=8765, debug=True)
