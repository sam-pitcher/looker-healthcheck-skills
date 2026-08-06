"""
Configuration settings for Looker Healthcheck Agent.
"""

import os
import json
from pathlib import Path

class LookerConfig:
    @staticmethod
    def load():
        # First priority: Environment variables
        base_url = os.getenv("LOOKERSDK_BASE_URL")
        client_id = os.getenv("LOOKERSDK_CLIENT_ID")
        client_secret = os.getenv("LOOKERSDK_CLIENT_SECRET")
        project_id = os.getenv("LOOKER_PROJECT_ID", "thelook-antigravity")
        
        # Second priority: Workspace settings.json
        if not (base_url and client_id and client_secret):
            settings_path = Path.home() / "Documents/Projects/thelook-antigravity/.vscode/settings.json"
            if settings_path.exists():
                with open(settings_path, "r") as f:
                    data = json.load(f)
                    base_url = base_url or data.get("looker.instanceURL")
                    client_id = client_id or data.get("looker.clientId")
                    client_secret = client_secret or data.get("looker.clientSecret")
                    project_id = data.get("looker.projectId", project_id)
        
        return {
            "base_url": (base_url or "").rstrip("/"),
            "client_id": client_id or "",
            "client_secret": client_secret or "",
            "project_id": project_id
        }
