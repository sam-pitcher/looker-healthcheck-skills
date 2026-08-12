"""
Dynamic Looker Skill Registry & Injection Engine.
Discovers, indexes, and injects pure knowledge playbooks from:
  1. skills/vendor/looker-skills/ (Official upstream Google Cloud Looker engineering skills)
  2. skills/custom/ (In-house healthcheck diagnostic playbooks and refactoring guides)
"""

import os
import glob
from pathlib import Path
from typing import Dict, Any, List, Optional

ROOT_DIR = Path(__file__).resolve().parent.parent

class LookerSkillRegistry:
    def __init__(self, base_dirs: Optional[List[str]] = None):
        if base_dirs:
            self.base_dirs = [Path(d) for d in base_dirs]
        else:
            self.base_dirs = [
                ROOT_DIR / ".agents" / "skills",
                ROOT_DIR / "skills" / "custom",
                ROOT_DIR / "skills" / "vendor" / "looker-skills" / "skills",
                ROOT_DIR / "skills"
            ]
        self.registry: Dict[str, Dict[str, Any]] = {}
        self.load_all_skills()

    def load_all_skills(self):
        """Discovers and indexes all pure knowledge SKILL.md files across IDE, vendor, and custom directories."""
        self.registry = {}
        for base_dir in self.base_dirs:
            if not base_dir.exists():
                continue
            
            pattern_upper = list(base_dir.rglob("SKILL.md"))
            pattern_lower = list(base_dir.rglob("skill.md"))
            
            for filepath in pattern_upper + pattern_lower:
                skill_data = self._parse_skill_file(filepath)
                if skill_data and "name" in skill_data:
                    name = skill_data["name"]
                    str_path = str(filepath)
                    if ".agents" in str_path:
                        source = "ide"
                    elif "vendor" in str_path:
                        source = "vendor"
                    else:
                        source = "custom"
                    
                    # Discover references if available in references/ subfolder
                    refs = {}
                    refs_dir = filepath.parent / "references"
                    if refs_dir.exists() and refs_dir.is_dir():
                        for ref_file in sorted(refs_dir.glob("*.md")):
                            try:
                                refs[ref_file.name] = ref_file.read_text(encoding="utf-8")
                            except Exception:
                                pass

                    if name not in self.registry:
                        self.registry[name] = {
                            "name": name,
                            "path": str(filepath),
                            "description": skill_data.get("description", ""),
                            "content": skill_data.get("body", ""),
                            "source": source,
                            "references": refs
                        }

    def _parse_skill_file(self, filepath: Path) -> Optional[Dict[str, Any]]:
        try:
            raw_text = filepath.read_text(encoding="utf-8")
            if raw_text.startswith("---"):
                parts = raw_text.split("---", 2)
                if len(parts) >= 3:
                    frontmatter = {}
                    try:
                        import yaml
                        frontmatter = yaml.safe_load(parts[1]) or {}
                    except Exception:
                        # Fallback simple line-by-line key: value parser
                        for line in parts[1].strip().split("\n"):
                            if ":" in line:
                                k, v = line.split(":", 1)
                                frontmatter[k.strip()] = v.strip().strip("'\"")
                    body = parts[2].strip()
                    frontmatter["body"] = body
                    if "name" not in frontmatter:
                        frontmatter["name"] = filepath.parent.name
                    return frontmatter
            return {
                "name": filepath.parent.name,
                "description": f"Looker engineering skill from {filepath.parent.name}",
                "body": raw_text.strip()
            }
        except Exception:
            return None

    def list_available_skills(self, source_filter: Optional[str] = None) -> List[Dict[str, str]]:
        """Returns a list of all indexed skills with their descriptions and sources."""
        items = []
        for k, v in sorted(self.registry.items()):
            if source_filter and v.get("source") != source_filter:
                continue
            items.append({
                "name": k,
                "description": v.get("description", ""),
                "source": v.get("source", "custom")
            })
        return items

    def get_skill(self, skill_name: str) -> Optional[Dict[str, Any]]:
        """Retrieves complete metadata and content for a given skill."""
        return self.registry.get(skill_name)

    def get_skill_prompt(self, skill_name: str) -> str:
        """Retrieves raw markdown prompt content for injection into LLM context."""
        skill = self.registry.get(skill_name)
        if skill:
            return skill.get("content", "")
        return ""

    def find_relevant_skills(self, topic: str) -> List[Dict[str, Any]]:
        """Finds matching skills by keyword search over name, description, and body content."""
        query = topic.lower()
        matches = []
        for name, data in self.registry.items():
            if query in name.lower() or query in data.get("description", "").lower() or query in data.get("content", "").lower()[:500]:
                matches.append(data)
        return matches

# Singleton instance for system-wide access
skill_registry = LookerSkillRegistry()

def get_skill_content(skill_name: str) -> str:
    """Tool function to dynamically retrieve official or custom Looker skill content for an agent."""
    content = skill_registry.get_skill_prompt(skill_name)
    skill = skill_registry.get_skill(skill_name)
    source = skill.get("source", "custom") if skill else "unknown"
    if content:
        return f"### 📘 Looker Skill (`{source}`): `{skill_name}`\n\n{content}"
    return f"Skill `{skill_name}` not found in registry. Available: {', '.join(list(skill_registry.registry.keys())[:10])}..."

def list_registered_skills(source: Optional[str] = None) -> str:
    """Tool function to list all registered Looker skills (vendor, custom, or all)."""
    skills = skill_registry.list_available_skills(source_filter=source)
    import json
    return f"### 📚 Registered Looker Skills ({len(skills)} Available - Filter: {source or 'All'}):\n```json\n{json.dumps(skills, indent=2)}\n```"
