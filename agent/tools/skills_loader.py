"""
Skills Loader: Ingests SKILL.md and reference benchmark files as Agent knowledge.
"""

from pathlib import Path
import re

def parse_frontmatter(content: str):
    """Simple parser for YAML frontmatter without external dependency requirement."""
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            raw_yaml = parts[1]
            body = parts[2].strip()
            metadata = {}
            for line in raw_yaml.split("\n"):
                if ":" in line:
                    k, v = line.split(":", 1)
                    metadata[k.strip()] = v.strip()
            return metadata, body
    return {}, content

class SkillsLoader:
    def __init__(self, skill_name: str = "looker-healthcheck"):
        self.skill_dir = Path(__file__).parents[2] / "skills" / skill_name

    def load_skill(self) -> dict:
        skill_file = self.skill_dir / "SKILL.md"
        if not skill_file.exists():
            raise FileNotFoundError(f"Skill file not found at {skill_file}")
        
        with open(skill_file, "r", encoding="utf-8") as f:
            metadata, body = parse_frontmatter(f.read())

        benchmarks_file = self.skill_dir / "references" / "pso_benchmarks.md"
        benchmarks_text = ""
        if benchmarks_file.exists():
            with open(benchmarks_file, "r", encoding="utf-8") as f:
                benchmarks_text = f.read()

        return {
            "name": metadata.get("name", "looker-healthcheck"),
            "description": metadata.get("description", ""),
            "instructions": body,
            "benchmarks_reference": benchmarks_text
        }
