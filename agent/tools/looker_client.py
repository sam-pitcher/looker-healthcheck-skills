"""
Looker API Client: Executes System Activity queries against the instance.
"""

import json
import ssl
import urllib.parse
import urllib.request
from typing import Dict, List, Any

class LookerClient:
    def __init__(self, config: Dict[str, str]):
        self.base_url = config["base_url"].rstrip("/")
        self.client_id = config["client_id"]
        self.client_secret = config["client_secret"]
        self.token = None
        self.ssl_context = ssl._create_unverified_context()

    def authenticate(self) -> str:
        login_url = f"{self.base_url}/api/4.0/login"
        payload = urllib.parse.urlencode({
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }).encode("utf-8")

        req = urllib.request.Request(login_url, data=payload, method="POST")
        with urllib.request.urlopen(req, context=self.ssl_context) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            self.token = data["access_token"]
            return self.token

    def run_query(self, model: str, view: str, fields: List[str], filters: Dict[str, str] = None, sorts: List[str] = None, limit: str = "50") -> List[Dict[str, Any]]:
        if not self.token:
            self.authenticate()

        query_url = f"{self.base_url}/api/4.0/queries/run/json"
        body = {
            "model": model,
            "view": view,
            "fields": fields,
            "limit": str(limit)
        }
        if filters:
            body["filters"] = filters
        if sorts:
            body["sorts"] = sorts

        req = urllib.request.Request(
            query_url,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"token {self.token}",
                "Content-Type": "application/json"
            },
            method="POST"
        )
        with urllib.request.urlopen(req, context=self.ssl_context) as resp:
            return json.loads(resp.read().decode("utf-8"))
