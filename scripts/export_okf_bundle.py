#!/usr/bin/env python3
"""
OKF v0.2 Bundle Exporter & Packaging Utility.
Packages validated OKF bundles into portable, checksum-verified distribution archives.
"""

import os
import sys
import json
import yaml
import tarfile
import hashlib
import argparse
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))


def sha256_file(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def export_bundle(bundle_info: dict, output_dir: Path) -> Path:
    bundle_id = bundle_info["id"]
    version = bundle_info.get("version", "1.0.0")
    print(f"📦 Packaging bundle: {bundle_id} (v{version})...")

    # 1. Collect files based on includes
    collected_files = []
    default_inc = bundle_info.get("path", f"bundle/{bundle_id}")
    includes = bundle_info.get("includes", [f"{default_inc}/**"])
    
    for inc in includes:
        if inc.endswith("/**"):
            base = ROOT_DIR / inc[:-3]
            if base.exists() and base.is_dir():
                for p in sorted(base.rglob("*")):
                    if p.is_file() and not p.name.startswith(".") and "__pycache__" not in str(p):
                        collected_files.append(p)
        else:
            exact = ROOT_DIR / inc
            if exact.exists() and exact.is_file():
                collected_files.append(exact)

    collected_files = sorted(list(set(collected_files)))
    print(f"   Collected {len(collected_files)} files.")

    # 3. Generate checksums
    checksums = {}
    for f in collected_files:
        rel = f.relative_to(ROOT_DIR)
        checksums[str(rel)] = sha256_file(f)

    # 4. Create archive
    output_dir.mkdir(parents=True, exist_ok=True)
    archive_name = f"{bundle_id}-v{version}.tar.gz"
    archive_path = output_dir / archive_name

    with tarfile.open(archive_path, "w:gz") as tar:
        for f in collected_files:
            rel = f.relative_to(ROOT_DIR)
            tar.add(f, arcname=str(rel))

        # Add bundle metadata manifest & checksums
        meta = dict(bundle_info)
        meta["file_count"] = len(collected_files)
        meta["checksums"] = checksums
        meta_bytes = json.dumps(meta, indent=2).encode("utf-8")

        import io
        ti = tarfile.TarInfo(name="bundle.json")
        ti.size = len(meta_bytes)
        tar.addfile(ti, io.BytesIO(meta_bytes))

    archive_size_kb = archive_path.stat().st_size / 1024
    archive_sha256 = sha256_file(archive_path)
    print(f"   ✅ Exported: {archive_path.name} ({archive_size_kb:.1f} KB)")
    print(f"      SHA256: {archive_sha256}")
    return archive_path


def main():
    parser = argparse.ArgumentParser(description="Export OKF v0.2 Knowledge Bundles.")
    parser.add_argument("--bundle", type=str, default="all", help="Target bundle ID or all")
    parser.add_argument("--output-dir", type=str, default="dist", help="Output directory for archives")
    args = parser.parse_args()

    manifest_file = ROOT_DIR / "manifest.yaml"
    if not manifest_file.exists():
        print(f"❌ Manifest not found at {manifest_file}", file=sys.stderr)
        sys.exit(1)

    with open(manifest_file, "r", encoding="utf-8") as f:
        manifest = yaml.safe_load(f)

    bundles = manifest.get("bundles", [])
    output_dir = ROOT_DIR / args.output_dir

    target_id = args.bundle.strip().lower()
    selected = bundles if target_id in ("all", "*") else [b for b in bundles if b.get("id") == target_id]

    if not selected:
        available_ids = [b.get('id') for b in bundles]
        print(f"❌ No matching bundle found for: {args.bundle}. Available: {available_ids}")
        sys.exit(1)

    cat_name = manifest.get('catalog_name', 'Knowledge Catalog')
    print(f"🚀 OKF v0.2 Bundle Exporter (Catalog: {cat_name})\n" + "=" * 65)
    exported = []
    for b in selected:
        out = export_bundle(b, output_dir)
        exported.append(out)

    print("=" * 65)
    print(f"🎉 Successfully exported {len(exported)} bundle(s) to `{args.output_dir}/`.\n")


if __name__ == "__main__":
    main()
