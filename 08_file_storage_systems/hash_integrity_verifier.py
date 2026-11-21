#!/usr/bin/env python3
"""
Directory Cryptographic Hash Manifest & Integrity Verifier
===========================================================
Creates cryptographic baselines and detects unauthorized modifications, bit rot, or tampering:
- Supports SHA-256, SHA-512, and MD5 algorithms
- Multi-threaded parallel file hashing
- Detects MODIFIED, MISSING, NEW, and CORRUPT files
- CI/CD & incident response ready with strict return codes

Keywords: hash manifest, integrity verifier, sha256 checksum, file tampering, backup verification
"""

import os
import sys
import json
import hashlib
import argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Tuple, Optional, Any


def hash_file_worker(file_path: Path, rel_path: str, algorithm: str = "sha256") -> Tuple[str, str, int]:
    """Compute hash and size of a single file."""
    hasher = getattr(hashlib, algorithm.lower())()
    try:
        sz = file_path.stat().st_size
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return rel_path, hasher.hexdigest(), sz
    except Exception:
        return rel_path, "", 0


def generate_manifest(target_dir: str, algorithm: str = "sha256", threads: int = 8) -> Dict[str, Any]:
    """Build a complete hash manifest of a directory."""
    root = Path(target_dir).resolve()
    if not root.exists():
        raise FileNotFoundError(f"Target directory not found: {target_dir}")

    file_tasks = []
    for dirpath, _, filenames in os.walk(root):
        for fname in filenames:
            full_path = Path(dirpath) / fname
            rel = str(full_path.relative_to(root)).replace("\\", "/")
            file_tasks.append((full_path, rel))

    manifest_entries = {}
    total_bytes = 0

    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = {executor.submit(hash_file_worker, fp, rel, algorithm): rel for fp, rel in file_tasks}
        for future in as_completed(futures):
            rel_path, digest, sz = future.result()
            if digest:
                manifest_entries[rel_path] = {
                    "hash": digest,
                    "size_bytes": sz
                }
                total_bytes += sz

    return {
        "root": str(root),
        "algorithm": algorithm.upper(),
        "total_files": len(manifest_entries),
        "total_bytes": total_bytes,
        "files": manifest_entries
    }


def verify_manifest(target_dir: str, manifest_data: Dict[str, Any], threads: int = 8, ignore_files: Optional[List[str]] = None) -> Dict[str, Any]:
    """Compare target directory against an existing hash manifest."""
    root = Path(target_dir).resolve()
    algorithm = manifest_data.get("algorithm", "SHA256").lower()
    expected_files = manifest_data.get("files", {})
    ignored = set(f.replace("\\", "/") for f in (ignore_files or []))

    current_manifest = generate_manifest(str(root), algorithm=algorithm, threads=threads)
    current_files = current_manifest["files"]

    matched = []
    modified = []
    missing = []
    new_files = []

    # Check expected files against current
    for rel_path, exp_info in expected_files.items():
        if rel_path in ignored:
            continue
        if rel_path not in current_files:
            missing.append(rel_path)
        else:
            cur_hash = current_files[rel_path]["hash"]
            if cur_hash == exp_info["hash"]:
                matched.append(rel_path)
            else:
                modified.append({
                    "file": rel_path,
                    "expected_hash": exp_info["hash"],
                    "actual_hash": cur_hash
                })

    # Check for newly added untracked files
    for rel_path in current_files.keys():
        if rel_path not in expected_files and rel_path not in ignored:
            new_files.append(rel_path)

    is_clean = (len(modified) == 0 and len(missing) == 0 and len(new_files) == 0)

    return {
        "verified_clean": is_clean,
        "total_expected": len(expected_files),
        "matched_count": len(matched),
        "modified_count": len(modified),
        "missing_count": len(missing),
        "new_count": len(new_files),
        "modified": modified,
        "missing": missing,
        "new_files": new_files
    }


def main():
    parser = argparse.ArgumentParser(
        description="Directory Cryptographic Hash Manifest & Integrity Verifier"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Generate command
    gen_p = subparsers.add_parser("generate", help="Create directory hash manifest")
    gen_p.add_argument("path", help="Target directory to hash")
    gen_p.add_argument("--algorithm", "-a", choices=["sha256", "sha512", "md5"], default="sha256",
                       help="Hash algorithm (default: sha256)")
    gen_p.add_argument("--output", "-o", required=True, help="Path to save manifest JSON")
    gen_p.add_argument("--threads", "-t", type=int, default=8, help="Hashing threads (default: 8)")

    # Verify command
    ver_p = subparsers.add_parser("verify", help="Verify directory against manifest")
    ver_p.add_argument("path", help="Target directory to verify")
    ver_p.add_argument("--manifest", "-m", required=True, help="Path to reference manifest JSON")
    ver_p.add_argument("--json", action="store_true", help="Output verification report in JSON")

    args = parser.parse_args()

    if args.command == "generate":
        print(f"[*] Generating {args.algorithm.upper()} manifest for '{args.path}'...")
        manifest = generate_manifest(args.path, algorithm=args.algorithm, threads=args.threads)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        print(f"[+] Hashed {manifest['total_files']} files ({manifest['total_bytes']:,} bytes).")
        print(f"[+] Saved manifest -> {args.output}")

    elif args.command == "verify":
        try:
            with open(args.manifest, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"[!] Failed to load manifest file: {e}", file=sys.stderr)
            sys.exit(1)

        print(f"[*] Verifying directory '{args.path}' against manifest...")
        manifest_rel = None
        try:
            m_path = Path(args.manifest).resolve()
            r_path = Path(args.path).resolve()
            if m_path.is_relative_to(r_path):
                manifest_rel = str(m_path.relative_to(r_path)).replace("\\", "/")
        except Exception:
            pass
        report = verify_manifest(args.path, data, ignore_files=[manifest_rel] if manifest_rel else None)

        if args.json:
            print(json.dumps(report, indent=2))
            sys.exit(0 if report["verified_clean"] else 1)

        print("\n=== Integrity Verification Report ===")
        print(f"  Status        : {'[PASSED] 100% Match' if report['verified_clean'] else '[FAILED] Discrepancies Found'}")
        print(f"  Matched Files : {report['matched_count']} / {report['total_expected']}")
        print(f"  Modified      : {report['modified_count']}")
        print(f"  Missing       : {report['missing_count']}")
        print(f"  New (Untracked): {report['new_count']}")

        if report["modified"]:
            print("\n  Modified Files (Tampered/Corrupt):")
            for m in report["modified"]:
                print(f"    - {m['file']}")
        if report["missing"]:
            print("\n  Missing Files:")
            for m in report["missing"]:
                print(f"    - {m}")
        if report["new_files"]:
            print("\n  New Untracked Files:")
            for n in report["new_files"]:
                print(f"    - {n}")

        sys.exit(0 if report["verified_clean"] else 1)


if __name__ == "__main__":
    main()
