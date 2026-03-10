# utils/deps.py

import sys
import subprocess
import importlib


def ensure_package(import_name: str, pip_name: str | None = None):
    """
    自动检查并安装 Python 包
    import_name: import 时的模块名
    pip_name: pip 安装时的包名，不传则默认和 import_name 一致
    """
    if pip_name is None:
        pip_name = import_name

    try:
        return importlib.import_module(import_name)
    except ImportError:
        print(f"📦 缺少依赖 {pip_name}，正在自动安装...")
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "-U", pip_name]
            )
            print(f"✅ 依赖 {pip_name} 安装完成")
            return importlib.import_module(import_name)
        except Exception as e:
            print(f"❌ 自动安装依赖失败: {pip_name} -> {e}")
            print(f"请手动执行：{sys.executable} -m pip install -U {pip_name}")
            sys.exit(1)