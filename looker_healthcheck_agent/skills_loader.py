"""
Skills & References Loader for Looker Healthcheck Skill.
"""

from pathlib import Path
from typing import Dict, Any

class SkillsLoader:
    def __init__(self, skill_name: str = "looker-healthcheck"):
        self.skill_dir = Path(__file__).parents[1] / "skills" / skill_name
        self.references_dir = self.skill_dir / "references"

    def load_skill(self) -> Dict[str, Any]:
        skill_file = self.skill_dir / "SKILL.md"
        body = ""
        if skill_file.exists():
            body = skill_file.read_text(encoding="utf-8")

        benchmarks_file = self.references_dir / "benchmarks.md"
        benchmarks_text = ""
        if benchmarks_file.exists():
            benchmarks_text = benchmarks_file.read_text(encoding="utf-8")

        references = self.load_all_references()

        return {
            "instructions": body,
            "benchmarks_reference": benchmarks_text,
            "references": references
        }

    def load_all_references(self) -> Dict[str, str]:
        refs = {}
        if self.references_dir.exists():
            for ref_file in sorted(self.references_dir.glob("*.md")):
                try:
                    refs[ref_file.name] = ref_file.read_text(encoding="utf-8")
                except Exception:
                    continue
        return refs

    def get_reference(self, reference_name: str) -> str:
        ref_file = self.references_dir / reference_name
        if ref_file.exists():
            return ref_file.read_text(encoding="utf-8")
        return f"Reference {reference_name} not found."
