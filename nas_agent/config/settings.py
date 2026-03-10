# config/settings.py

MODEL_NAME = "lfm2:24b-a2b"
MAX_TURNS = 8

SHOW_THINKING = False
THINK_LEVEL = False   # False / True / "low" / "medium" / "high"

APP_NAME = "NAS Agent"
APP_VERSION = "0.1.0"

SYSTEM_PROMPT = """
你是一个运行在私人 NAS 上的高级智能管家。

你的核心原则：
1. 绝对保护主人的数据隐私，默认所有处理都在本地完成。
2. 当前处于测试阶段，你没有文件删除、移动、修改、下载、上传权限。
3. 不能伪造执行结果；没做过就是没做过，不知道就是不知道。
4. 回复风格：极客、干练、直接、少废话。
5. 能一句话说清的，绝不说两句。
6. 遇到 Linux、Docker、NAS、网络、自动化问题，优先给可执行方案。
7. 遇到危险操作，必须先提醒风险。
8. 你优先帮助主人查看系统状态，而不是空谈概念。
"""
# MoviePilot 配置
MOVIEPILOT_BASE_URL = "http://192.168.1.137:3333"
MOVIEPILOT_SOURCE = "agent"
MOVIEPILOT_API_TOKEN = "WAOQOuEN2Ikm6PcT4y6iIw"
MOVIEPILOT_TIMEOUT = 10