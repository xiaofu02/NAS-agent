# tools/moviepilot/openapi.py

from tools.moviepilot.client import MoviePilotClient


def get_moviepilot_openapi() -> dict:
    """
    读取 MoviePilot 的 OpenAPI 文档，并提取路径列表
    """
    client = MoviePilotClient()

    result = client.get("/openapi.json")
    if not result.get("ok"):
        return {
            "ok": False,
            "name": "moviepilot_openapi",
            "error": "无法读取 MoviePilot OpenAPI",
            "data": {
                "base_url": client.base_url,
                "details": result,
            }
        }

    payload = result.get("json")
    if not isinstance(payload, dict):
        return {
            "ok": False,
            "name": "moviepilot_openapi",
            "error": "OpenAPI 返回不是 JSON 对象",
            "data": {
                "base_url": client.base_url,
                "raw": result.get("text", "")[:500],
            }
        }

    paths = payload.get("paths", {}) or {}
    path_items = []

    for path, methods in paths.items():
        method_list = []
        if isinstance(methods, dict):
            for method_name in methods.keys():
                method_list.append(str(method_name).upper())

        path_items.append({
            "path": path,
            "methods": sorted(method_list),
        })

    path_items.sort(key=lambda x: x["path"])

    return {
        "ok": True,
        "name": "moviepilot_openapi",
        "data": {
            "base_url": client.base_url,
            "auth_mode": result.get("auth_mode"),
            "url": result.get("url"),
            "title": payload.get("info", {}).get("title", ""),
            "version": payload.get("info", {}).get("version", ""),
            "path_count": len(path_items),
            "paths": path_items,
            "raw_json": payload,
        }
    }