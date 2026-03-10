import requests

BAIDU_QIANFAN_API_KEY = "bce-v3/ALTAK-jmBH4LZ71IWfIEp8GJQFK/81968a51ac30b27629f9c7ad4d078e20baae5c15"
BAIDU_SEARCH_URL = "https://qianfan.baidubce.com/v2/ai_search/chat/completions"
TIMEOUT = 30


def _clean_text(text: str, max_len: int = 160) -> str:
    text = (text or "").replace("\n", " ").replace("\r", " ").strip()
    while "  " in text:
        text = text.replace("  ", " ")
    if len(text) > max_len:
        text = text[:max_len] + "..."
    return text


def _dedupe_references(references: list) -> list:
    seen = set()
    result = []

    for ref in references or []:
        url = (ref.get("url") or "").strip()
        title = (ref.get("title") or "").strip()

        key = url or title
        if not key:
            continue

        if key in seen:
            continue

        seen.add(key)
        result.append(ref)

    return result


def _summarize_references_naturally(query: str, references: list) -> str:
    refs = _dedupe_references(references)[:5]

    if not refs:
        return "这次没有查到可用结果。"

    lines = []

    # 第一段：整体判断
    lines.append(f"我帮你查了一下“{query}”，目前搜索结果主要集中在下面几个重点：\n")

    # 第二段：重点内容
    for idx, ref in enumerate(refs[:3], 1):
        title = (ref.get("title") or "").strip()
        website = (ref.get("website") or "").strip()
        date = (ref.get("date") or "").strip()
        snippet = _clean_text(ref.get("snippet") or ref.get("content") or "", max_len=140)

        meta = []
        if website:
            meta.append(website)
        if date:
            meta.append(date)

        meta_text = ""
        if meta:
            meta_text = f"（{' / '.join(meta)}）"

        paragraph = f"{idx}. {title}{meta_text}"
        if snippet:
            paragraph += f"\n   {snippet}"

        lines.append(paragraph)

    # 第三段：总体提示
    lines.append("\n整体来看，这几条结果的方向比较一致，但如果你要做进一步判断，还是建议优先参考权威媒体或原始来源。")

    # 第四段：参考来源
    lines.append("\n参考来源：")
    for i, ref in enumerate(refs, 1):
        title = ref.get("title", "无标题")
        url = ref.get("url", "")
        lines.append(f"{i}. {title} {url}")

    return "\n".join(lines)


def search_web(query: str) -> dict:
    query = (query or "").strip()

    if not query:
        return {
            "ok": False,
            "name": "baidu_web_search",
            "error": "缺少搜索内容。用法：/search 你的问题"
        }

    if not BAIDU_QIANFAN_API_KEY:
        return {
            "ok": False,
            "name": "baidu_web_search",
            "error": "未配置 BAIDU_QIANFAN_API_KEY"
        }

    headers = {
        "Authorization": f"Bearer {BAIDU_QIANFAN_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "messages": [
            {"role": "user", "content": query}
        ],
        "stream": False
    }

    try:
        resp = requests.post(
            BAIDU_SEARCH_URL,
            headers=headers,
            json=payload,
            timeout=TIMEOUT
        )
        resp.raise_for_status()
        data = resp.json()

        references = data.get("references", []) or []
        summary = _summarize_references_naturally(query, references)

        return {
            "ok": True,
            "name": "baidu_web_search",
            "query": query,
            "answer": summary,
            "references": references,
            "raw": data
        }

    except requests.HTTPError:
        return {
            "ok": False,
            "name": "baidu_web_search",
            "query": query,
            "error": f"HTTP 错误: {resp.text}"
        }
    except Exception as e:
        return {
            "ok": False,
            "name": "baidu_web_search",
            "query": query,
            "error": str(e)
        }