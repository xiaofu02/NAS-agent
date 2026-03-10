# tools/moviepilot/get/tool.py

from tools.moviepilot.client import MoviePilotClient


def moviepilot_get(path: str) -> dict:
    if not path:
        return {
            "ok": False,
            "name": "mp_get",
            "error": "缺少路径参数"
        }

    if not path.startswith("/"):
        path = "/" + path

    client = MoviePilotClient()
    result = client.get(path)

    if not result.get("ok"):
        return {
            "ok": False,
            "name": "mp_get",
            "error": "请求失败",
            "data": {
                "base_url": client.base_url,
                "path": path,
                "details": result,
            }
        }

    return {
        "ok": True,
        "name": "mp_get",
        "data": {
            "base_url": client.base_url,
            "path": path,
            "auth_mode": result.get("auth_mode"),
            "url": result.get("url"),
            "status_code": result.get("status_code"),
            "json": result.get("json"),
            "text_preview": (result.get("text") or "")[:2000],
        }
    }