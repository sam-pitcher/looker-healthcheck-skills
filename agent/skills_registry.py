"""
Open Knowledge Format (OKF v0.2) Dynamic Knowledge Registry & Injection Engine.
Discovers, indexes, validates, and injects pure knowledge playbooks, references, and
attested computations across the knowledge catalog.

Conforms strictly to the Open Knowledge Format (OKF v0.2) specification:
- https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing?e=a
- https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md
"""

import os
import re
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

ROOT_DIR = Path(__file__).resolve().parent.parent


def parse_yaml_frontmatter(text: str) -> Tuple[Optional[Dict[str, Any]], str]:
    """
    Robust YAML frontmatter parser conforming to OKF §4.1.
    Supports PyYAML if available, with a dependency-free pure Python fallback.
    """
    trimmed = text.strip()
    if not trimmed.startswith("---"):
        return None, trimmed

    parts = trimmed.split("---", 2)
    if len(parts) < 3:
        return None, trimmed

    fm_raw = parts[1].strip()
    body = parts[2].strip()

    # 1. Try PyYAML if installed
    try:
        import yaml
        loaded = yaml.safe_load(fm_raw)
        if isinstance(loaded, dict):
            return loaded, body
    except Exception:
        pass

    # 2. Dependency-free pure Python YAML parser
    data: Dict[str, Any] = {}
    lines = fm_raw.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            i += 1
            continue

        if ":" in line and not line.startswith(" ") and not line.startswith("-"):
            k, v = line.split(":", 1)
            k = k.strip()
            v = v.strip()

            if not v:
                # Multiline list or mapping
                items: List[Any] = []
                i += 1
                while i < len(lines) and (lines[i].startswith("  -") or lines[i].startswith("    ")):
                    subline = lines[i]
                    sub_stripped = subline.strip()
                    if sub_stripped.startswith("-"):
                        item_content = sub_stripped[1:].strip()
                        if ":" in item_content:
                            ik, iv = item_content.split(":", 1)
                            dict_item = {ik.strip(): _clean_yaml_val(iv.strip())}
                            i += 1
                            while i < len(lines) and lines[i].startswith("    ") and not lines[i].strip().startswith("-"):
                                if ":" in lines[i]:
                                    dk, dv = lines[i].strip().split(":", 1)
                                    dict_item[dk.strip()] = _clean_yaml_val(dv.strip())
                                i += 1
                            items.append(dict_item)
                            continue
                        else:
                            items.append(_clean_yaml_val(item_content))
                    i += 1
                data[k] = items
                continue
            elif v.startswith("[") and v.endswith("]"):
                inner = v[1:-1].strip()
                if not inner:
                    data[k] = []
                else:
                    data[k] = [_clean_yaml_val(x.strip()) for x in inner.split(",") if x.strip()]
            elif v.startswith("{") and v.endswith("}"):
                inner = v[1:-1].strip()
                d_obj: Dict[str, Any] = {}
                for pair in inner.split(","):
                    if ":" in pair:
                        pk, pv = pair.split(":", 1)
                        d_obj[pk.strip()] = _clean_yaml_val(pv.strip())
                data[k] = d_obj
            else:
                data[k] = _clean_yaml_val(v)
        i += 1

    return data, body


def _clean_yaml_val(val: str) -> Any:
    """Converts a raw scalar string to typed Python boolean, int, float, or unquoted string."""
    v = val.strip()
    if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
        return v[1:-1]
    if v.lower() == "true":
        return True
    if v.lower() == "false":
        return False
    if v.isdigit():
        return int(v)
    try:
        return float(v)
    except ValueError:
        return v


def compute_trust_tier(verified_entries: Any) -> str:
    """
    Computes OKF Trust Tier according to §5.3:
    - No verified key ⇒ unverified
    - verified by non-human: actors only ⇒ machine-confirmed
    - verified by a human:<id> actor ⇒ human-reviewed
    """
    if not verified_entries:
        return "unverified"

    # Normalize bare mapping to single-element list (§5.2)
    entries = [verified_entries] if isinstance(verified_entries, dict) else (verified_entries if isinstance(verified_entries, list) else [])
    if not entries:
        return "unverified"

    has_human = False
    has_verifier = False

    for entry in entries:
        if isinstance(entry, dict):
            actor = str(entry.get("by", "")).strip()
        else:
            actor = str(entry).strip()

        if actor:
            has_verifier = True
            if actor.startswith("human:"):
                has_human = True

    if has_human:
        return "human-reviewed"
    elif has_verifier:
        return "machine-confirmed"
    return "unverified"


def check_is_stale(stale_after_str: Optional[str]) -> bool:
    """
    Determines if concept is stale according to §5.5 (now >= stale_after).
    """
    if not stale_after_str:
        return False
    try:
        # Normalize ISO-8601 string
        clean_ts = str(stale_after_str).replace("Z", "+00:00")
        stale_dt = datetime.fromisoformat(clean_ts)
        now_dt = datetime.now(timezone.utc)
        return now_dt >= stale_dt
    except Exception:
        return False


class LookerSkillRegistry:
    """
    Open Knowledge Format (OKF v0.2) Catalog & Skill Registry.
    Indexes, queries, and verifies knowledge bundles, playbooks, references, and attested computations.
    """

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
        self.concepts: Dict[str, Dict[str, Any]] = {}
        self.registry: Dict[str, Dict[str, Any]] = {}
        self.indexes: Dict[str, Dict[str, Any]] = {}
        self.logs: Dict[str, Dict[str, Any]] = {}
        self.load_all_skills()

    def load_all_skills(self):
        """
        Discovers, parses, and indexes all OKF concepts, playbooks, references,
        indexes, and logs across all configured bundle directories.
        """
        self.concepts = {}
        self.registry = {}
        self.indexes = {}
        self.logs = {}

        for base_dir in self.base_dirs:
            if not base_dir.exists():
                continue

            for md_file in base_dir.rglob("*.md"):
                rel_to_root = str(md_file.relative_to(ROOT_DIR)) if str(ROOT_DIR) in str(md_file) else str(md_file)
                file_name = md_file.name

                # 1. Reserved: index.md (§8)
                if file_name == "index.md":
                    self._parse_index_file(md_file, rel_to_root)
                    continue

                # 2. Reserved: log.md (§9)
                if file_name == "log.md":
                    self._parse_log_file(md_file, rel_to_root)
                    continue

                # 3. Concept Documents (§4)
                concept = self._parse_concept_file(md_file, rel_to_root)
                if concept:
                    cid = concept["id"]
                    self.concepts[cid] = concept
                    # Also index by simple filename without path
                    self.concepts[md_file.name] = concept
                    self.concepts[md_file.stem] = concept

                    # Maintain backward compatibility with legacy registry keys
                    name_key = concept.get("name") or md_file.parent.name
                    if name_key not in self.registry or concept.get("type") == "Skill":
                        self.registry[name_key] = concept

        # Populate nested playbooks and references for legacy skill definitions
        for skill_name, skill_data in list(self.registry.items()):
            skill_path = Path(skill_data.get("path", ""))
            if skill_path.exists():
                playbooks = {}
                pb_dir = skill_path.parent / "playbooks"
                if pb_dir.exists() and pb_dir.is_dir():
                    for pb_file in sorted(pb_dir.glob("*.md")):
                        try:
                            playbooks[pb_file.name] = pb_file.read_text(encoding="utf-8")
                        except Exception:
                            pass

                refs = {}
                ref_dir = skill_path.parent / "references"
                if ref_dir.exists() and ref_dir.is_dir():
                    for ref_file in sorted(ref_dir.glob("*.md")):
                        try:
                            refs[ref_file.name] = ref_file.read_text(encoding="utf-8")
                        except Exception:
                            pass

                comps = {}
                comp_dir = skill_path.parent / "computations"
                if comp_dir.exists() and comp_dir.is_dir():
                    for comp_file in sorted(comp_dir.glob("*.md")):
                        try:
                            comps[comp_file.name] = comp_file.read_text(encoding="utf-8")
                        except Exception:
                            pass

                skill_data["playbooks"] = playbooks
                skill_data["references"] = refs
                skill_data["computations"] = comps

    def _parse_concept_file(self, filepath: Path, rel_path: str) -> Optional[Dict[str, Any]]:
        """Parses a markdown concept document into an OKF v0.2 structured dictionary."""
        try:
            raw_text = filepath.read_text(encoding="utf-8")
            fm, body = parse_yaml_frontmatter(raw_text)
            fm = fm or {}

            # Concept ID: relative path without .md (§2)
            concept_id = rel_path[:-3] if rel_path.endswith(".md") else rel_path

            # Source tagging
            if ".agents" in rel_path:
                source = "ide"
            elif "vendor" in rel_path:
                source = "vendor"
            else:
                source = "custom"

            # Derive type (§4.1)
            concept_type = fm.get("type")
            if not concept_type:
                if filepath.name.lower() == "skill.md":
                    concept_type = "Skill"
                elif "playbooks" in rel_path:
                    concept_type = "Playbook"
                elif "references" in rel_path:
                    concept_type = "Reference"
                elif "computations" in rel_path:
                    concept_type = "Attested Computation"
                else:
                    concept_type = "Concept"

            # Derive title
            title = fm.get("title")
            if not title:
                # Infer from first H1 header in body or filename
                h1_match = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
                if h1_match:
                    title = h1_match.group(1).strip()
                else:
                    title = filepath.stem.replace("_", " ").title()

            # Trust and Lifecycle families (§5)
            verified = fm.get("verified")
            verified_list = [verified] if isinstance(verified, dict) else (verified if isinstance(verified, list) else [])
            trust_tier = compute_trust_tier(verified_list)
            stale_after = fm.get("stale_after")
            is_stale = check_is_stale(stale_after)
            status = fm.get("status", "stable")

            # Attested Computation fields (§10)
            runtime = fm.get("runtime")
            parameters = fm.get("parameters", [])
            executor = fm.get("executor")
            attester = fm.get("attester")
            computation = fm.get("computation")

            # If inline computation, extract from # Computation section
            if concept_type == "Attested Computation" and not computation:
                comp_match = re.search(r"#\s+Computation\s+```(?:\w+)?\n([\s\S]*?)```", body)
                if comp_match:
                    computation = comp_match.group(1).strip()

            concept = {
                "id": concept_id,
                "name": fm.get("name", filepath.parent.name if filepath.name.lower() == "skill.md" else filepath.stem),
                "type": concept_type,
                "title": title,
                "description": fm.get("description", f"Looker knowledge concept from {filepath.name}"),
                "resource": fm.get("resource"),
                "tags": fm.get("tags", []),
                "status": status,
                "stale_after": stale_after,
                "is_stale": is_stale,
                "generated": fm.get("generated", {}),
                "verified": verified_list,
                "trust_tier": trust_tier,
                "sources": fm.get("sources", []),
                "usage_window": fm.get("usage_window", {}),
                "runtime": runtime,
                "parameters": parameters,
                "executor": executor,
                "attester": attester,
                "computation": computation,
                "content": body,
                "body": body,
                "path": str(filepath),
                "rel_path": rel_path,
                "source": source,
                "frontmatter": fm
            }
            return concept
        except Exception:
            return None

    def _parse_index_file(self, filepath: Path, rel_path: str):
        """Parses an index.md file for progressive disclosure (§8, §12)."""
        try:
            raw_text = filepath.read_text(encoding="utf-8")
            fm, body = parse_yaml_frontmatter(raw_text)
            fm = fm or {}
            
            dir_key = str(filepath.parent.relative_to(ROOT_DIR)) if str(ROOT_DIR) in str(filepath) else str(filepath.parent)
            self.indexes[dir_key] = {
                "path": str(filepath),
                "rel_path": rel_path,
                "okf_version": fm.get("okf_version", "0.2" if "okf_version" in raw_text else None),
                "body": body,
                "raw_text": raw_text
            }
        except Exception:
            pass

    def _parse_log_file(self, filepath: Path, rel_path: str):
        """Parses a log.md file for update history (§9)."""
        try:
            raw_text = filepath.read_text(encoding="utf-8")
            dir_key = str(filepath.parent.relative_to(ROOT_DIR)) if str(ROOT_DIR) in str(filepath) else str(filepath.parent)
            self.logs[dir_key] = {
                "path": str(filepath),
                "rel_path": rel_path,
                "body": raw_text
            }
        except Exception:
            pass

    def get_concept(self, concept_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves an OKF concept document by ID, relative path, or filename."""
        if not concept_id:
            return None

        cid = str(concept_id).strip()
        if cid.startswith("file://"):
            cid = cid[7:]
            if str(ROOT_DIR) in cid:
                cid = cid[len(str(ROOT_DIR)):].lstrip("/")
        if cid.startswith("/"):
            cid = cid.lstrip("/")

        clean_id = cid[:-3] if cid.endswith(".md") else cid
        stem_id = Path(cid).stem

        for candidate in [cid, clean_id, stem_id]:
            if candidate in self.concepts:
                return self.concepts[candidate]

        # Search by suffix match (e.g. 'playbook_looker_performance')
        for k, v in self.concepts.items():
            if k == cid or k == clean_id or k.endswith(clean_id) or k.endswith(f"/{clean_id}") or (stem_id and k.endswith(f"/{stem_id}")):
                return v
        return None

    def get_skill(self, skill_name: str) -> Optional[Dict[str, Any]]:
        """Retrieves skill metadata dictionary (backward-compatible)."""
        # Check registry first
        if skill_name in self.registry:
            return self.registry[skill_name]
        return self.get_concept(skill_name)

    def get_skill_prompt(self, skill_name: str) -> str:
        """
        Retrieves markdown content for LLM prompt injection, searching skills,
        playbooks, references, and computations.
        """
        concept = self.get_concept(skill_name)
        if concept:
            return concept.get("content") or concept.get("body", "")

        # Fallback to searching playbooks / references inside registered skills
        target_name = skill_name if skill_name.endswith(".md") else f"{skill_name}.md"
        for s in self.registry.values():
            if target_name in s.get("playbooks", {}):
                return s["playbooks"][target_name]
            if target_name in s.get("references", {}):
                return s["references"][target_name]
            if target_name in s.get("computations", {}):
                return s["computations"][target_name]
        return ""

    def get_attested_computation(self, computation_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves an Attested Computation concept by ID (§10)."""
        concept = self.get_concept(computation_id)
        if concept and concept.get("type") == "Attested Computation":
            return concept
        # Search among all concepts of type Attested Computation
        for c in self.concepts.values():
            if c.get("type") == "Attested Computation":
                if computation_id.lower() in c.get("id", "").lower() or computation_id.lower() in c.get("title", "").lower():
                    return c
        return None

    def get_directory_index(self, dir_path: Optional[str] = None) -> Optional[str]:
        """Returns the content of an index.md file for progressive disclosure (§8)."""
        key = dir_path or "skills"
        clean_key = key.strip("/")
        if clean_key in self.indexes:
            return self.indexes[clean_key]["raw_text"]
        for k, v in self.indexes.items():
            if k.endswith(clean_key) or clean_key.endswith(k):
                return v["raw_text"]
        return None

    def get_directory_log(self, dir_path: Optional[str] = None) -> Optional[str]:
        """Returns the update log for a directory scope (§9)."""
        key = dir_path or "skills"
        clean_key = key.strip("/")
        if clean_key in self.logs:
            return self.logs[clean_key]["body"]
        for k, v in self.logs.items():
            if k.endswith(clean_key) or clean_key.endswith(k):
                return v["body"]
        return None

    def find_by_type(self, concept_type: str) -> List[Dict[str, Any]]:
        """Finds all concepts of a given OKF type (e.g. 'Playbook', 'Attested Computation')."""
        target = concept_type.lower()
        seen = set()
        results = []
        for c in self.concepts.values():
            cid = c.get("id")
            if cid and cid not in seen and c.get("type", "").lower() == target:
                seen.add(cid)
                results.append(c)
        return results

    def find_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        """Finds all concepts matching a specific categorization tag (§4.1)."""
        target = tag.lower()
        seen = set()
        results = []
        for c in self.concepts.values():
            cid = c.get("id")
            if cid and cid not in seen:
                tags = [str(t).lower() for t in c.get("tags", [])]
                if target in tags:
                    seen.add(cid)
                    results.append(c)
        return results

    def find_relevant_skills(self, topic: str) -> List[Dict[str, Any]]:
        """Performs keyword search across concept titles, descriptions, and bodies."""
        query = topic.lower()
        seen = set()
        matches = []
        for c in self.concepts.values():
            cid = c.get("id")
            if not cid or cid in seen:
                continue
            name = c.get("name", "")
            title = c.get("title", "")
            desc = c.get("description", "")
            tags = " ".join([str(t) for t in c.get("tags", [])])
            body = c.get("content", "")[:600]

            if (query in name.lower() or query in title.lower() or 
                query in desc.lower() or query in tags.lower() or query in body.lower()):
                seen.add(cid)
                matches.append(c)
        return matches

    def list_available_skills(self, source_filter: Optional[str] = None) -> List[Dict[str, str]]:
        """Returns a summary list of all registered skills and playbooks."""
        items = []
        seen = set()
        for k, v in sorted(self.registry.items()):
            if source_filter and v.get("source") != source_filter:
                continue
            name = v.get("name", k)
            if name in seen:
                continue
            seen.add(name)
            items.append({
                "name": name,
                "type": v.get("type", "Skill"),
                "title": v.get("title", name),
                "description": v.get("description", ""),
                "trust_tier": v.get("trust_tier", "unverified"),
                "source": v.get("source", "custom"),
                "playbooks_count": len(v.get("playbooks", {})),
                "references_count": len(v.get("references", {}))
            })
        return items

    def validate_okf_conformance(self, bundle_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Validates the knowledge bundle against the 3 normative Conformance Rules of OKF v0.2 (§11):
        1. Every non-reserved .md file contains parseable YAML frontmatter.
        2. Every frontmatter block contains a non-empty `type` field.
        3. Every reserved filename (index.md, log.md) follows §8 and §9 structure.
        """
        target_path = (ROOT_DIR / bundle_dir).resolve() if bundle_dir else (ROOT_DIR / "skills").resolve()
        bundle_root_resolved = (ROOT_DIR / "skills").resolve()
        issues: List[Dict[str, str]] = []
        total_files = 0
        concepts_checked = 0
        indexes_checked = 0
        logs_checked = 0

        if not target_path.exists():
            return {
                "conformant": False,
                "error": f"Bundle directory not found: {target_path}",
                "issues": [{"file": str(target_path), "error": "Directory does not exist"}]
            }

        for md_file in sorted(target_path.rglob("*.md")):
            total_files += 1
            resolved_file = md_file.resolve()
            try:
                rel_file = str(resolved_file.relative_to(ROOT_DIR.resolve()))
            except ValueError:
                rel_file = str(resolved_file)
            content = md_file.read_text(encoding="utf-8")

            if md_file.name == "index.md":
                indexes_checked += 1
                # §8 & §12: No frontmatter permitted except at the bundle-root index.md
                if resolved_file == (bundle_root_resolved / "index.md"):
                    # Bundle root index may declare okf_version (§12)
                    fm, _ = parse_yaml_frontmatter(content)
                    if fm and "okf_version" not in fm:
                        issues.append({"file": rel_file, "rule": "§8", "issue": "Root index.md frontmatter must only declare okf_version."})
                else:
                    if content.strip().startswith("---"):
                        issues.append({"file": rel_file, "rule": "§8", "issue": "Non-root index.md MUST NOT contain YAML frontmatter."})
                continue

            if md_file.name == "log.md":
                logs_checked += 1
                # §9: Update history must use YYYY-MM-DD headings
                if not re.search(r"##\s+\d{4}-\d{2}-\d{2}", content):
                    issues.append({"file": rel_file, "rule": "§9", "issue": "log.md date headings must use ISO-8601 YYYY-MM-DD format."})
                continue

            # Non-reserved concept documents (§11 Rule 1 & 2)
            concepts_checked += 1
            if not content.strip().startswith("---"):
                issues.append({"file": rel_file, "rule": "§11.1", "issue": "Missing YAML frontmatter block delimited by '---'."})
                continue

            fm, body = parse_yaml_frontmatter(content)
            if fm is None:
                issues.append({"file": rel_file, "rule": "§11.1", "issue": "Malformed or unparseable YAML frontmatter block."})
                continue

            if not fm.get("type"):
                issues.append({"file": rel_file, "rule": "§11.2", "issue": "Required 'type' field is missing or empty."})

            # Check Attested Computation contract (§10)
            if fm.get("type") == "Attested Computation":
                if not fm.get("runtime"):
                    issues.append({"file": rel_file, "rule": "§10.2", "issue": "Attested Computation missing required 'runtime' field."})
                if "# Computation" not in body and not fm.get("computation"):
                    issues.append({"file": rel_file, "rule": "§10.3", "issue": "Attested Computation missing computation body block or 'computation' path."})

        is_conformant = len(issues) == 0
        return {
            "conformant": is_conformant,
            "okf_version": "0.2",
            "bundle_root": str(target_path),
            "total_files_audited": total_files,
            "concepts_audited": concepts_checked,
            "index_files_audited": indexes_checked,
            "log_files_audited": logs_checked,
            "issues_count": len(issues),
            "issues": issues
        }

    # --------------------------------------------------------------------------
    # OKF Concept Graph Engine (§6, §10, §11)
    # --------------------------------------------------------------------------
    def build_concept_graph(self) -> Dict[str, Any]:
        """
        Constructs an in-memory Directed Concept Graph from all indexed OKF concepts,
        sources, cross-links, and attested computation execution bindings.
        """
        nodes: Dict[str, Dict[str, Any]] = {}
        edges: List[Dict[str, str]] = []
        adjacency: Dict[str, List[str]] = {}

        for cid, c in self.concepts.items():
            if "/" not in cid and not cid.endswith(".md"):
                continue  # Skip short stem aliases to prevent duplicate nodes

            nodes[cid] = {
                "id": cid,
                "title": c.get("title", cid),
                "type": c.get("type", "Concept"),
                "status": c.get("status", "stable"),
                "trust_tier": c.get("trust_tier", "unverified"),
                "source": c.get("source", "custom"),
                "runtime": c.get("runtime"),
                "path": c.get("rel_path", "")
            }
            if cid not in adjacency:
                adjacency[cid] = []

            # 1. Provenance Attribution Edges (from frontmatter sources: [...])
            for s in c.get("sources", []):
                raw_target = s.get("resource")
                if raw_target:
                    target_c = self.get_concept(raw_target)
                    target_id = target_c.get("id") if target_c else raw_target
                    edges.append({
                        "source": cid,
                        "target": target_id,
                        "relationship": "sourced_from",
                        "label": s.get("title", "Upstream Source")
                    })
                    adjacency[cid].append(target_id)

            # 2. Markdown Cross-Links (§6 [Title](target))
            body = c.get("body", "")
            links = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", body)
            for link_text, raw_target in links:
                if not raw_target.startswith("http") and not raw_target.startswith("#") and not raw_target.startswith("mailto:"):
                    clean_target = raw_target.strip()
                    target_c = self.get_concept(clean_target)
                    target_id = target_c.get("id") if target_c else clean_target
                    edges.append({
                        "source": cid,
                        "target": target_id,
                        "relationship": "references",
                        "label": link_text
                    })
                    adjacency[cid].append(target_id)

            # 3. Attested Computation Execution Edges (§10)
            if c.get("type") == "Attested Computation":
                executor = c.get("executor", {}).get("resource") if isinstance(c.get("executor"), dict) else None
                attester = c.get("attester", {}).get("resource") if isinstance(c.get("attester"), dict) else None
                if executor:
                    edges.append({"source": cid, "target": str(executor), "relationship": "executed_by", "label": "Executor Tool"})
                    adjacency[cid].append(str(executor))
                if attester:
                    edges.append({"source": cid, "target": str(attester), "relationship": "attested_by", "label": "Attester"})
                    adjacency[cid].append(str(attester))

        # Deduplicate edges
        deduped_edges = []
        seen_edges = set()
        for e in edges:
            key = (e["source"], e["target"], e["relationship"])
            if key not in seen_edges:
                seen_edges.add(key)
                deduped_edges.append(e)

        # Synthesize nodes for external resources, tools, and explores so graph is fully connected
        for e in deduped_edges:
            for endpoint in (e["source"], e["target"]):
                if endpoint not in nodes:
                    ep_str = str(endpoint)
                    if ep_str.startswith("http"):
                        etype = "External Source"
                        label = ep_str.split("/")[-1] or ep_str
                    elif "INFORMATION_SCHEMA" in ep_str or "system__activity" in ep_str:
                        etype = "Data Source / View"
                        label = ep_str.split(".")[-1]
                    elif ep_str.startswith("agent/tools") or ep_str.endswith(".py"):
                        etype = "Execution Tool"
                        label = ep_str.split("/")[-1]
                    else:
                        etype = "Resource"
                        label = ep_str.split("/")[-1]

                    nodes[endpoint] = {
                        "id": endpoint,
                        "title": label,
                        "type": etype,
                        "status": "external",
                        "trust_tier": "machine-confirmed" if "INFORMATION_SCHEMA" in ep_str else "unverified",
                        "source": "environment",
                        "runtime": None,
                        "path": ep_str
                    }

        return {
            "nodes": nodes,
            "edges": deduped_edges,
            "adjacency": adjacency,
            "total_nodes": len(nodes),
            "total_edges": len(deduped_edges)
        }

    def get_related_concepts(self, concept_id: str, max_depth: int = 1) -> List[Dict[str, Any]]:
        """
        Finds neighboring concepts connected to concept_id in the Concept Graph.
        Allows agents to perform multi-hop semantic navigation across playbooks, references, and computations.
        """
        graph = self.build_concept_graph()
        target_concept = self.get_concept(concept_id)
        if not target_concept:
            return []

        target_id = target_concept.get("id")
        target_stem = Path(concept_id).stem
        related_ids = set()

        for edge in graph["edges"]:
            s, t = edge["source"], edge["target"]
            if s == target_id or s.endswith(target_stem) or target_stem in s:
                related_ids.add(t)
            elif t == target_id or t.endswith(target_stem) or target_stem in t:
                related_ids.add(s)

        results = []
        for rid in sorted(related_ids):
            c = self.get_concept(rid)
            if c:
                results.append({
                    "id": c.get("id"),
                    "title": c.get("title"),
                    "type": c.get("type"),
                    "trust_tier": c.get("trust_tier"),
                    "description": c.get("description"),
                    "runtime": c.get("runtime")
                })
        return results

    def find_graph_path(self, start_concept: str, target_concept: str) -> List[str]:
        """
        Calculates the shortest semantic reasoning path between two concepts using BFS graph traversal.
        """
        graph = self.build_concept_graph()
        s_concept = self.get_concept(start_concept)
        t_concept = self.get_concept(target_concept)

        if not s_concept or not t_concept:
            return []

        start_id = s_concept.get("id")
        target_id = t_concept.get("id")

        if start_id == target_id:
            return [start_id]

        queue = [[start_id]]
        visited = {start_id}

        while queue:
            path = queue.pop(0)
            node = path[-1]

            neighbors = graph["adjacency"].get(node, [])
            for neighbor in neighbors:
                # Resolve neighbor concept ID if relative path
                resolved_neighbor = neighbor
                c = self.get_concept(neighbor)
                if c:
                    resolved_neighbor = c.get("id")

                if resolved_neighbor == target_id:
                    return path + [resolved_neighbor]

                if resolved_neighbor not in visited:
                    visited.add(resolved_neighbor)
                    queue.append(path + [resolved_neighbor])

        return []

    def export_concept_graph_mermaid(self, root_concept: Optional[str] = None, max_nodes: int = 25) -> str:
        """
        Generates a clean Mermaid node-link diagram representing the concept graph or a focused sub-graph.
        """
        graph = self.build_concept_graph()
        lines = ["graph TD"]
        lines.append("    %% Concept Nodes")

        included_nodes = set()
        if root_concept:
            r = self.get_concept(root_concept)
            if r:
                root_id = r.get("id")
                included_nodes.add(root_id)
                related = self.get_related_concepts(root_concept)
                for rel in related:
                    included_nodes.add(rel["id"])
        else:
            # Pick prominent playbooks and computations
            for nid, n in graph["nodes"].items():
                if n["type"] in ("Playbook", "Attested Computation", "Skill") or len(included_nodes) < max_nodes:
                    included_nodes.add(nid)
                if len(included_nodes) >= max_nodes:
                    break

        node_keys = {}
        for idx, nid in enumerate(included_nodes):
            n = graph["nodes"].get(nid)
            if not n:
                continue
            key = f"N{idx}"
            node_keys[nid] = key
            safe_title = n["title"].replace('"', "'")
            ntype = n["type"]
            lines.append(f'    {key}["{safe_title}<br/><i>({ntype})</i>"]')

        lines.append("    %% Semantic Edges")
        for edge in graph["edges"]:
            s, t, rel = edge["source"], edge["target"], edge["relationship"]
            if s in node_keys and t in node_keys:
                lines.append(f'    {node_keys[s]} -->|"{rel}"| {node_keys[t]}')

        return "\n".join(lines)

    def export_concept_graph_json(self) -> Dict[str, Any]:
        """
        Exports the entire Concept Graph in standard D3.js / Cytoscape / DocGen JSON format.
        """
        graph = self.build_concept_graph()
        json_nodes = []
        for nid, data in graph["nodes"].items():
            json_nodes.append({
                "id": nid,
                "label": data["title"],
                "type": data["type"],
                "trust_tier": data["trust_tier"],
                "status": data["status"],
                "source": data["source"],
                "runtime": data["runtime"]
            })

        json_links = []
        for e in graph["edges"]:
            json_links.append({
                "source": e["source"],
                "target": e["target"],
                "relationship": e["relationship"],
                "label": e.get("label", "")
            })

        return {
            "nodes": json_nodes,
            "links": json_links,
            "total_nodes": len(json_nodes),
            "total_links": len(json_links)
        }


# Singleton registry instance for global system access
skill_registry = LookerSkillRegistry()


# ==============================================================================
# Agent ADK Tool Bindings
# ==============================================================================

def get_skill_content(skill_name: str) -> str:
    """
    Tool function: Dynamically retrieves official or custom Looker skill/playbook content,
    attested computation contracts, or reference documentation for an agent.
    """
    content = skill_registry.get_skill_prompt(skill_name)
    concept = skill_registry.get_concept(skill_name)
    
    if content:
        ctype = concept.get("type", "Playbook") if concept else "Playbook"
        source = concept.get("source", "custom") if concept else "custom"
        trust = concept.get("trust_tier", "unverified") if concept else "unverified"
        title = concept.get("title", skill_name) if concept else skill_name
        
        header = f"### 📘 Looker Knowledge Concept: `{title}`\n"
        header += f"- **Type:** `{ctype}` | **Source:** `{source}` | **Trust Tier:** `{trust}`\n\n"
        return header + content
    
    available = list(skill_registry.registry.keys())[:10]
    return f"Skill, playbook, or concept `{skill_name}` not found in OKF registry. Available: {', '.join(available)}..."


def list_registered_skills(source: Optional[str] = None) -> str:
    """
    Tool function: Lists all registered Looker skills and playbooks with OKF metadata.
    """
    skills = skill_registry.list_available_skills(source_filter=source)
    return f"### 📚 OKF Registered Looker Knowledge ({len(skills)} Concepts - Filter: {source or 'All'}):\n```json\n{json.dumps(skills, indent=2)}\n```"


def get_okf_index(directory: Optional[str] = None) -> str:
    """
    Tool function: Retrieves a directory index (index.md) for progressive disclosure (§8).
    Allows agents to see available concepts without polluting context with entire files.
    """
    index_text = skill_registry.get_directory_index(directory)
    if index_text:
        return f"### 📑 OKF Progressive Disclosure Index (`{directory or 'skills'}`):\n\n{index_text}"
    return f"No index.md found for scope: `{directory or 'skills'}`."


def get_okf_attested_computation(computation_id: str) -> str:
    """
    Tool function: Retrieves the contract and sanctioned computation for an Attested Computation concept (§10).
    """
    comp = skill_registry.get_attested_computation(computation_id)
    if comp:
        output = {
            "id": comp.get("id"),
            "title": comp.get("title"),
            "runtime": comp.get("runtime"),
            "parameters": comp.get("parameters"),
            "trust_tier": comp.get("trust_tier"),
            "status": comp.get("status"),
            "computation": comp.get("computation"),
            "executor": comp.get("executor"),
            "attester": comp.get("attester")
        }
        return f"### ⚡ Attested Computation Contract (`{comp.get('title')}`):\n```json\n{json.dumps(output, indent=2)}\n```\n\n#### 📜 Computation Body:\n\n{comp.get('body')}"
    return f"Attested computation `{computation_id}` not found."


def validate_okf_knowledge_catalog(bundle_path: Optional[str] = None) -> str:
    """
    Tool function: Runs full §11 conformance verification across the knowledge bundle.
    """
    report = skill_registry.validate_okf_conformance(bundle_path)
    status = "🟢 CONFORMANT (OKF v0.2)" if report["conformant"] else "🔴 NON-CONFORMANT"
    return f"### 🛡️ OKF v0.2 Knowledge Catalog Conformance Report: {status}\n```json\n{json.dumps(report, indent=2)}\n```"


def get_okf_concept_graph(concept_id: Optional[str] = None) -> str:
    """
    Tool function: Retrieves the connected Concept Graph for multi-hop semantic navigation (§6).
    Returns related playbooks, references, and computations connected by provenance or cross-links.
    
    Args:
        concept_id: Optional concept name or relative path. If omitted, returns global graph topology.
    """
    if concept_id:
        related = skill_registry.get_related_concepts(concept_id)
        mermaid = skill_registry.export_concept_graph_mermaid(root_concept=concept_id)
        return (
            f"### 🕸️ OKF Concept Subgraph for `{concept_id}` ({len(related)} Connected Concepts):\n\n"
            f"```mermaid\n{mermaid}\n```\n\n"
            f"#### 🔗 Connected Concepts:\n```json\n{json.dumps(related, indent=2)}\n```"
        )

    graph = skill_registry.build_concept_graph()
    mermaid = skill_registry.export_concept_graph_mermaid(max_nodes=15)
    return (
        f"### 🌐 OKF Global Concept Graph Topology:\n"
        f"- **Total Concept Nodes:** {graph['total_nodes']}\n"
        f"- **Total Semantic Edges:** {graph['total_edges']}\n\n"
        f"```mermaid\n{mermaid}\n```"
    )


def find_diagnostic_graph_path(start_concept: str, target_concept: str) -> str:
    """
    Tool function: Calculates the shortest diagnostic reasoning path between two concepts.
    Allows the agent to traverse from a symptom/finding to the exact remediation recipe.
    """
    path = skill_registry.find_graph_path(start_concept, target_concept)
    if not path:
        return f"No direct semantic path found between `{start_concept}` and `{target_concept}` in the concept graph."

    steps = " ➔ ".join(f"`{p}`" for p in path)
    return f"### 🧭 Diagnostic Graph Path ({len(path)} hops):\n\n{steps}"

