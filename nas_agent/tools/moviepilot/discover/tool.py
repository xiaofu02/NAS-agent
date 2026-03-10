# tools/moviepilot/discover/tool.py

import re
from urllib.parse import urljoin

from tools.moviepilot.client import MoviePilotClient
from utils.deps import ensure_package

requests = ensure_package("requests")

SCRIPT_SRC_RE = re.compile(r'<script[^>]+src=["\']([^"\']+)["\']', re.IGNORECASE)
API_PATH_RE = re.compile(r'(/api/[A-Za-z0-9_\-./?=&]+)')


def _fetch_text(url: str, headers: dict | None = None, params: dict | None = None, timeout: int = 10):
    try:
        resp = requests.get(url, headers=headers or {}, params=params or {}, timeout=timeout)
        return {
            "ok": resp.status_code < 400,
            "status_code": resp.status_code,
            "url": resp.url,
            "text": resp.text,
        }
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "url": url,
            "text": "",
        }


def _build_auth_headers_and_params(client: MoviePilotClient):
    headers = {}
    params = {}

    if client.api_token:
        headers["apikey"] = client.api_token
        params["token"] = client.api_token

    if client.source:
        params["source"] = client.source

    return headers, params


def discover_moviepilot_routes() -> dict:
    client = MoviePilotClient()
    headers, params = _build_auth_headers_and_params(client)

    docs_url = f"{client.base_url}/docs"
    docs_resp = _fetch_text(docs_url, headers=headers, params=params, timeout=client.timeout)

    if not docs_resp.get("ok"):
        return {
            "ok": False,
            "name": "moviepilot_discover",
            "error": "无法读取 MoviePilot docs 页面",
            "data": {
                "base_url": client.base_url,
                "docs_result": docs_resp,
            }
        }

    html = docs_resp.get("text", "")
    script_srcs = SCRIPT_SRC_RE.findall(html)

    script_urls = []
    for src in script_srcs:
        script_urls.append(urljoin(client.base_url + "/", src))

    discovered_paths = set()
    fetched_scripts = []

    for script_url in script_urls[:20]:
        js_resp = _fetch_text(script_url, headers=headers, params={}, timeout=client.timeout)
        fetched_scripts.append({
            "url": script_url,
            "ok": js_resp.get("ok", False),
            "status_code": js_resp.get("status_code"),
        })

        if not js_resp.get("ok"):
            continue

        js_text = js_resp.get("text", "")
        for match in API_PATH_RE.findall(js_text):
            cleaned = match.strip().strip('"').strip("'").strip(")").strip("]")
            if cleaned.startswith("/api/"):
                discovered_paths.add(cleaned)

    sorted_paths = sorted(discovered_paths)

    return {
        "ok": True,
        "name": "moviepilot_discover",
        "data": {
            "base_url": client.base_url,
            "docs_url": docs_resp.get("url"),
            "script_count": len(script_urls),
            "fetched_scripts": fetched_scripts,
            "path_count": len(sorted_paths),
            "paths": sorted_paths,
            "html_preview": html[:1500],
        }
    }