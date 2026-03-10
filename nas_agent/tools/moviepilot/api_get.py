# tools/moviepilot/api_get.py

from tools.moviepilot.client import MoviePilotClient


def get_moviepilot_api(path: str) -> dict:
    """
    对指定 MoviePilot API 路径做只读 GET
    path 示例:
      /api/v1/system/global
      /api/v1/system/message
    """
    if not path:
        return {
            "ok": False,
            "name": "moviepilot_api_get",
            "error": "未提供 path"
        }

    if not path.startswith("/"):
        path = "/" + path

    client = MoviePilotClient()
    result = client.get(path)

    if not result.get("ok"):
        return {
            "ok": False,
            "name": "moviepilot_api_get",
            "error": "API GET 失败",
            "data": {
                "base_url": client.base_url,
                "path": path,
                "details": result,
            }
        }

    return {
        "ok": True,
        "name": "moviepilot_api_get",
        "data": {
            "base_url": client.base_url,
            "path": path,
            "auth_mode": result.get("auth_mode"),
            "url": result.get("url"),
            "status_code": result.get("status_code"),
            "json": result.get("json"),
            "text_preview": (result.get("text") or "")[:1000],
        }
    }