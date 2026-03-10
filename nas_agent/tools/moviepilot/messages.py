# tools/moviepilot/messages.py

from tools.moviepilot.client import MoviePilotClient


def _normalize_message_item(item: dict) -> dict:
    """
    尽量把 MoviePilot 返回的消息统一成固定结构
    不强依赖具体字段名，避免版本差异导致直接炸掉
    """
    if not isinstance(item, dict):
        return {"raw": item}

    return {
        "title": item.get("title") or item.get("subject") or item.get("name") or "",
        "text": item.get("text") or item.get("content") or item.get("message") or "",
        "type": item.get("mtype") or item.get("type") or item.get("category") or "",
        "channel": item.get("channel") or "",
        "source": item.get("source") or "",
        "date": item.get("date") or item.get("time") or item.get("created_at") or item.get("create_time") or "",
        "raw": item,
    }


def get_moviepilot_messages(limit: int = 10) -> dict:
    """
    读取 MoviePilot 消息列表
    优先使用 /api/v1/system/message
    """
    client = MoviePilotClient()

    result = client.get("/api/v1/system/message")
    if not result.get("ok"):
        return {
            "ok": False,
            "name": "moviepilot_messages",
            "error": "无法读取 MoviePilot 消息",
            "data": {
                "base_url": client.base_url,
                "details": result
            }
        }

    payload = result.get("json")
    items = []

    # 兼容不同返回格式
    if isinstance(payload, list):
        items = payload
    elif isinstance(payload, dict):
        for key in ["data", "items", "list", "results", "messages"]:
            value = payload.get(key)
            if isinstance(value, list):
                items = value
                break

        # 有些接口可能直接是 {"data": {...}} 但不是列表
        if not items and "data" in payload and isinstance(payload["data"], dict):
            items = [payload["data"]]

    normalized = [_normalize_message_item(x) for x in items[:limit]]

    return {
        "ok": True,
        "name": "moviepilot_messages",
        "data": {
            "base_url": client.base_url,
            "count": len(normalized),
            "auth_mode": result.get("auth_mode"),
            "url": result.get("url"),
            "messages": normalized,
            "raw_json": payload,
        }
    }