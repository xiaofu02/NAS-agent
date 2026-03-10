# tools/moviepilot/status/tool.py

from tools.moviepilot.client import MoviePilotClient


def get_moviepilot_status() -> dict:
    client = MoviePilotClient()

    probes = [
        {"name": "docs", "path": "/docs"},
        {"name": "openapi", "path": "/openapi.json"},
    ]

    results = []
    for probe in probes:
        result = client.get(probe["path"])
        results.append({
            "probe": probe["name"],
            "path": probe["path"],
            **result
        })

    working_probe = next((r for r in results if r.get("ok")), None)

    return {
        "ok": working_probe is not None,
        "name": "moviepilot_status",
        "data": {
            "base_url": client.base_url,
            "working_probe": working_probe,
            "results": results,
        }
    }