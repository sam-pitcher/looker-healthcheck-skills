"""
Looker API Client for Healthcheck Diagnostics.
"""

import os
import json
import urllib3
from pathlib import Path
from typing import Dict, Any, List, Optional
import requests

# Suppress insecure SSL warnings for local developer environments
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class LookerDiagnosticsClient:
    def __init__(self):
        # 1. Try env vars
        self.base_url = os.getenv("LOOKERSDK_BASE_URL", "").rstrip("/")
        self.client_id = os.getenv("LOOKERSDK_CLIENT_ID", "")
        self.client_secret = os.getenv("LOOKERSDK_CLIENT_SECRET", "")
        
        # 2. Fallback to settings.json
        if not (self.base_url and self.client_id and self.client_secret):
            settings_path = Path.home() / "Documents/Projects/thelook-antigravity/.vscode/settings.json"
            if settings_path.exists():
                try:
                    with open(settings_path, "r", encoding="utf-8") as f:
                        settings = json.load(f)
                    self.base_url = settings.get("looker.connection.instanceUrl", "").rstrip("/")
                    self.client_id = settings.get("looker.connection.clientId", "")
                    self.client_secret = settings.get("looker.connection.clientSecret", "")
                except Exception:
                    pass

        self.token = None

    def authenticate(self):
        if not self.base_url:
            raise ValueError("Looker Base URL is not configured.")
        login_url = f"{self.base_url}/api/4.0/login"
        resp = requests.post(login_url, data={"client_id": self.client_id, "client_secret": self.client_secret}, verify=False)
        if resp.status_code != 200:
            raise RuntimeError(f"Looker Auth failed: {resp.status_code} {resp.text}")
        self.token = resp.json().get("access_token")

    def run_query(self, model: str, view: str, fields: List[str], filters: Optional[Dict[str, str]] = None, sorts: Optional[List[str]] = None, limit: str = "500") -> List[Dict[str, Any]]:
        if not self.token:
            self.authenticate()
        url = f"{self.base_url}/api/4.0/queries/run/json"
        body = {
            "model": model,
            "view": view,
            "fields": fields,
            "filters": filters or {},
            "sorts": sorts or [],
            "limit": limit
        }
        headers = {"Authorization": f"token {self.token}", "Content-Type": "application/json"}
        resp = requests.post(url, headers=headers, json=body, verify=False)
        if resp.status_code != 200:
            raise RuntimeError(f"Query error {resp.status_code}: {resp.text}")
        return resp.json()
