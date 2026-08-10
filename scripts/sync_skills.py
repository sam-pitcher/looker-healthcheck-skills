#!/usr/bin/env python3
"""
Syncs upstream Looker engineering skills from official GitHub repository:
https://github.com/looker-open-source/looker-skills
"""

import os
import sys
import subprocess
from pathlib import Path

REPO_URL = "https://github.com/looker-open-source/looker-skills.git"
ROOT_DIR = Path(__file__).resolve().parent.parent
TARGET_DIR = ROOT_DIR / "skills" / "vendor" / "looker-skills"

def sync_looker_skills() -> bool:
    """Clones or pulls the latest skills from looker-open-source/looker-skills."""
    TARGET_DIR.parent.mkdir(parents=True, exist_ok=True)
    
    if not TARGET_DIR.exists():
        print(f"📦 Cloning upstream looker-skills from {REPO_URL} into {TARGET_DIR}...")
        try:
            subprocess.run(["git", "clone", "--depth", "1", REPO_URL, str(TARGET_DIR)], check=True)
            print("✅ Successfully cloned looker-skills.")
            return True
        except Exception as e:
            print(f"⚠️ Failed to clone looker-skills: {e}", file=sys.stderr)
            return False
    else:
        print(f"🔄 Pulling latest updates for {TARGET_DIR}...")
        try:
            subprocess.run(["git", "-C", str(TARGET_DIR), "pull"], check=True)
            print("✅ Successfully updated looker-skills.")
            return True
        except Exception as e:
            print(f"⚠️ Failed to pull looker-skills: {e}", file=sys.stderr)
            return False

if __name__ == "__main__":
    success = sync_looker_skills()
    sys.exit(0 if success else 1)
