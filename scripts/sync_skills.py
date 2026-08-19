#!/usr/bin/env python3
"""
Manifest-Driven Skill Synchronization Engine (Manifest-as-Code).
Reads skills.yaml and performs selective, shallow Sparse-Checkouts to download
ONLY the required vendor skill folders into skills/vendor/.

Gold Standard Guarantees:
1. Storage Footprint: Zero disk bloat via git sparse-checkout (--filter=blob:none).
2. Clean Git Tree: Eliminates submodule tracking issues, detached HEAD states, and CI recursion.
3. Declarative Versioning: All external dependencies, branches/refs, and paths are versioned in skills.yaml.
"""

import os
import sys
import shutil
import argparse
import subprocess
from pathlib import Path
from typing import Dict, Any, List

ROOT_DIR = Path(__file__).resolve().parent.parent
MANIFEST_PATH = ROOT_DIR / "skills.yaml"
VENDOR_DIR = ROOT_DIR / "skills" / "vendor"

def _parse_simple_yaml(text: str) -> Dict[str, Any]:
    """Lightweight fallback YAML parser for skills.yaml if PyYAML is unavailable."""
    skills = []
    current_skill = None
    current_list_key = None
    
    for line in text.splitlines():
        trimmed = line.strip()
        if not trimmed or trimmed.startswith("#"):
            continue
        
        if trimmed.startswith("- name:"):
            if current_skill:
                skills.append(current_skill)
            name_val = trimmed.split(":", 1)[1].strip().strip("'\"")
            current_skill = {"name": name_val, "paths": []}
            current_list_key = None
        elif current_skill is not None:
            if ":" in trimmed and not trimmed.startswith("-"):
                k, v = trimmed.split(":", 1)
                k = k.strip()
                v = v.strip().strip("'\"")
                if v:
                    current_skill[k] = v
                else:
                    current_list_key = k
            elif trimmed.startswith("- ") and current_list_key:
                val = trimmed[2:].strip().strip("'\"")
                if current_list_key not in current_skill:
                    current_skill[current_list_key] = []
                current_skill[current_list_key].append(val)
                
    if current_skill:
        skills.append(current_skill)
    return {"vendor_skills": skills}

def load_manifest() -> Dict[str, Any]:
    """Loads and parses skills.yaml with PyYAML or built-in fallback."""
    if not MANIFEST_PATH.exists():
        print(f"❌ Error: Manifest file not found at {MANIFEST_PATH}", file=sys.stderr)
        sys.exit(1)
    
    try:
        import yaml
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except ImportError:
        raw = MANIFEST_PATH.read_text(encoding="utf-8")
        return _parse_simple_yaml(raw)

def sync_vendor_skill(skill_cfg: Dict[str, Any], force_clean: bool = False) -> bool:
    """Performs sparse clone or update for a single vendor skill definition."""
    name = skill_cfg.get("name")
    source = skill_cfg.get("source")
    ref = skill_cfg.get("ref", "main")
    target_rel = skill_cfg.get("target", f"skills/vendor/{name}")
    paths: List[str] = skill_cfg.get("paths", [])
    
    target_dir = ROOT_DIR / target_rel
    target_dir.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"📦 [Vendor Skill: {name}]")
    print(f"   • Source: {source} (ref: {ref})")
    print(f"   • Target: {target_dir.relative_to(ROOT_DIR)}")
    print(f"   • Selective Paths ({len(paths)}): {', '.join(paths)}")
    
    if force_clean and target_dir.exists():
        print(f"   🧹 Cleaning existing directory...")
        shutil.rmtree(target_dir, ignore_errors=True)
        
    if not target_dir.exists() or not (target_dir / ".git").exists():
        print(f"   ⬇️ Initializing sparse clone...")
        try:
            # Step 1: Clone without blobs, sparse-initialized
            subprocess.run([
                "git", "clone",
                "--depth", "1",
                "--filter=blob:none",
                "--sparse",
                "--branch", ref,
                source, str(target_dir)
            ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # Step 2: Set exact sparse checkout paths
            if paths:
                subprocess.run([
                    "git", "-C", str(target_dir),
                    "sparse-checkout", "set", *paths
                ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
            print(f"   ✅ Successfully sparse-cloned {name} ({len(paths)} directories extracted).")
            return True
        except subprocess.CalledProcessError as e:
            err_msg = e.stderr.strip() if e.stderr else str(e)
            print(f"   ⚠️ Failed to clone {name}: {err_msg}", file=sys.stderr)
            if "googlesource.com" in source:
                print(f"   💡 Note: GoogleSource authentication required. Please generate your git cookie at:\n      https://google-cloud-professional-services.googlesource.com/new-password", file=sys.stderr)
            return False
    else:
        print(f"   🔄 Updating existing sparse checkout...")
        try:
            if paths:
                subprocess.run([
                    "git", "-C", str(target_dir),
                    "sparse-checkout", "set", *paths
                ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
            subprocess.run([
                "git", "-C", str(target_dir),
                "pull", "--depth", "1"
            ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f"   ✅ Up to date ({len(paths)} paths active).")
            return True
        except subprocess.CalledProcessError as e:
            err_msg = e.stderr.strip() if e.stderr else str(e)
            print(f"   ⚠️ Failed to update {name}: {err_msg}", file=sys.stderr)
            return False

def main():
    parser = argparse.ArgumentParser(description="Sync external vendor skills via Manifest-as-Code (skills.yaml).")
    parser.add_argument("--clean", action="store_true", help="Wipe and re-clone vendor directories.")
    parser.add_argument("--skill", type=str, default=None, help="Sync only a specific skill by name.")
    args = parser.parse_args()
    
    manifest = load_manifest()
    vendor_skills = manifest.get("vendor_skills", [])
    
    if not vendor_skills:
        print("ℹ️ No vendor skills declared in skills.yaml.")
        return
        
    print(f"🚀 Starting Manifest-Driven Skill Synchronization ({len(vendor_skills)} declared)...\n")
    
    results = {}
    for skill_cfg in vendor_skills:
        name = skill_cfg.get("name")
        if args.skill and name != args.skill:
            continue
        success = sync_vendor_skill(skill_cfg, force_clean=args.clean)
        results[name] = success
        print("-" * 60)
        
    print("\n📊 Final Synchronization Report:")
    for name, ok in results.items():
        status = "✅ ACTIVE (SPARSE)" if ok else "⚠️ PENDING AUTH / ACTION"
        print(f"  • {name:<25}: {status}")

if __name__ == "__main__":
    main()
