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
        
        # 2. Fallback to standard Looker CLI config if present
        if not (self.base_url and self.client_id and self.client_secret):
            cli_config_path = Path.home() / ".config/looker-cli/config.yaml"
            if cli_config_path.exists():
                try:
                    import yaml
                    with open(cli_config_path, "r", encoding="utf-8") as f:
                        cfg = yaml.safe_load(f)
                    current_ctx = cfg.get("current_context", "default")
                    ctx = cfg.get("contexts", {}).get(current_ctx, {})
                    self.base_url = self.base_url or ctx.get("base_url", "").rstrip("/")
                    self.client_id = self.client_id or ctx.get("client_id", "")
                    self.client_secret = self.client_secret or ctx.get("client_secret", "")
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
