# tools/moviepilot/client.py

from config.settings import (
    MOVIEPILOT_BASE_URL,
    MOVIEPILOT_API_TOKEN,
    MOVIEPILOT_TIMEOUT,
    MOVIEPILOT_SOURCE,
)
from utils.deps import ensure_package

requests = ensure_package("requests")


class MoviePilotClient:
    def __init__(
        self,
        base_url: str = None,
        api_token: str = None,
        timeout: int = None,
        source: str = None,
    ):
        self.base_url = (base_url or MOVIEPILOT_BASE_URL).rstrip("/")
        self.api_token = api_token if api_token is not None else MOVIEPILOT_API_TOKEN
        self.timeout = timeout or MOVIEPILOT_TIMEOUT
        self.source = source if source is not None else MOVIEPILOT_SOURCE

    def _candidate_requests(self, path: str):
        """
        生成多种鉴权方式的请求参数
        兼容：
        - apikey header
        - Authorization Bearer
        - ?token=
        - 无鉴权（仅做探测）
        """
        url = f"{self.base_url}{path}"
        candidates = []

        if self.api_token:
            candidates.append({
                "url": url,
                "headers": {"apikey": self.api_token},
                "params": {},
                "auth_mode": "apikey_header",
            })

            candidates.append({
                "url": url,
                "headers": {"Authorization": f"Bearer {self.api_token}"},
                "params": {},
                "auth_mode": "bearer_header",
            })

            token_params = {"token": self.api_token}
            if self.source:
                token_params["source"] = self.source

            candidates.append({
                "url": url,
                "headers": {},
                "params": token_params,
                "auth_mode": "token_query",
            })

        candidates.append({
            "url": url,
            "headers": {},
            "params": {},
            "auth_mode": "no_auth",
        })

        return candidates

    def get(self, path: str):
        """
        依次尝试多种鉴权方式，返回第一个成功结果
        """
        errors = []

        for candidate in self._candidate_requests(path):
            try:
                resp = requests.get(
                    candidate["url"],
                    headers=candidate["headers"],
                    params=candidate["params"],
                    timeout=self.timeout,
                )

                if resp.status_code < 400:
                    return {
                        "ok": True,
                        "status_code": resp.status_code,
                        "auth_mode": candidate["auth_mode"],
                        "url": resp.url,
                        "text": resp.text,
                        "json": self._safe_json(resp),
                    }

                errors.append({
                    "auth_mode": candidate["auth_mode"],
                    "status_code": resp.status_code,
                    "text": resp.text[:300],
                    "url": resp.url,
                })

            except Exception as e:
                errors.append({
                    "auth_mode": candidate["auth_mode"],
                    "error": str(e),
                    "url": candidate["url"],
                })

        return {
            "ok": False,
            "errors": errors,
        }

    @staticmethod
    def _safe_json(resp):
        try:
            return resp.json()
        except Exception:
            return None