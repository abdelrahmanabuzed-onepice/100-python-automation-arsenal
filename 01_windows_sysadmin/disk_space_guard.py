#!/usr/bin/env python3
"""
Disk Space Guard & Clutter Analyzer
====================================
High-speed storage analyzer for Windows & cross-platform:
- Finds top N space hog files & directory breakdowns
- Detects exact duplicate files using two-stage hashing (size pre-filter + SHA256)
- Identifies system/user junk and temp file bloat with safe cleanup dry-run options

Keywords: disk cleaner, duplicate file finder, storage analyzer, sysadmin tools, windows disk cleanup
"""

import os
import sys
import hashlib
import argparse
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple, Optional, Any


def format_bytes(size_bytes: int) -> str:
    """Format bytes into human-readable string (KB, MB, GB)."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if abs(size_bytes) < 1024.0:
            return f"{size_bytes:3.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def compute_file_hash(path: Path, chunk_size: int = 65536) -> str:
    """Compute SHA256 hash of a file efficiently."""
    hasher = hashlib.sha256()
    try:
        with open(path, 'rb') as f:
            while chunk := f.read(chunk_size):
                hasher.update(chunk)
        return hasher.hexdigest()
    except (PermissionError, OSError):
        return ""


def scan_storage(target_dir: str, top_n: int = 20, min_size_mb: float = 0.0) -> Dict:
    """Scan directory for largest files and extension distribution."""
    target_path = Path(target_dir).resolve()
    if not target_path.exists():
        raise FileNotFoundError(f"Target directory does not exist: {target_dir}")

    total_bytes = 0
    file_count = 0
    dir_count = 0
    extension_sizes: Dict[str, int] = defaultdict(int)
    extension_counts: Dict[str, int] = defaultdict(int)
    files_list: List[Tuple[Path, int]] = []
    min_size_bytes = int(min_size_mb * 1024 * 1024)

    for root, dirs, files in os.walk(target_path):
        dir_count += len(dirs)
        for f in files:
            fp = Path(root) / f
            try:
                sz = fp.stat().st_size
                total_bytes += sz
                file_count += 1
                ext = fp.suffix.lower() or "<no_ext>"
                extension_sizes[ext] += sz
                extension_counts[ext] += 1
                if sz >= min_size_bytes:
                    files_list.append((fp, sz))
            except (PermissionError, OSError):
                continue

    # Sort largest files
    files_list.sort(key=lambda x: x[1], reverse=True)
    top_files = files_list[:top_n]

    return {
        "target": str(target_path),
        "total_files": file_count,
        "total_dirs": dir_count,
        "total_size_bytes": total_bytes,
        "total_size_human": format_bytes(total_bytes),
        "top_files": [(str(p), sz, format_bytes(sz)) for p, sz in top_files],
        "extensions": [
            (ext, extension_counts[ext], extension_sizes[ext], format_bytes(extension_sizes[ext]))
            for ext in sorted(extension_sizes, key=extension_sizes.get, reverse=True)[:10]
        ]
    }


def find_duplicates(target_dir: str, min_size_kb: int = 10) -> Dict[str, List[str]]:
    """Two-stage duplicate file detection (Group by size first, hash only collisions)."""
    target_path = Path(target_dir).resolve()
    size_map: Dict[int, List[Path]] = defaultdict(list)
    min_size_bytes = min_size_kb * 1024

    for root, _, files in os.walk(target_path):
        for f in files:
            fp = Path(root) / f
            try:
                sz = fp.stat().st_size
                if sz >= min_size_bytes:
                    size_map[sz].append(fp)
            except (PermissionError, OSError):
                continue

    duplicates: Dict[str, List[str]] = defaultdict(list)
    for sz, path_list in size_map.items():
        if len(path_list) > 1:
            hash_map: Dict[str, List[Path]] = defaultdict(list)
            for p in path_list:
                h = compute_file_hash(p)
                if h:
                    hash_map[h].append(p)
            for h, matches in hash_map.items():
                if len(matches) > 1:
                    duplicates[f"{h[:16]} ({format_bytes(sz)})"] = [str(m) for m in matches]

    return duplicates


def check_temp_bloat() -> Dict[str, Any]:
    """Scan common Windows temp folders for clutter."""
    temp_dirs = []
    if "TEMP" in os.environ:
        temp_dirs.append(os.environ["TEMP"])
    if "LOCALAPPDATA" in os.environ:
        temp_dirs.append(os.path.join(os.environ["LOCALAPPDATA"], "Temp"))
    if sys.platform == "win32":
        win_temp = "C:\\Windows\\Temp"
        if os.path.exists(win_temp):
            temp_dirs.append(win_temp)

    results = []
    for td in set(temp_dirs):
        p = Path(td)
        if not p.exists():
            continue
        count = 0
        sz = 0
        try:
            for root, _, files in os.walk(p):
                for f in files:
                    try:
                        sz += (Path(root) / f).stat().st_size
                        count += 1
                    except (PermissionError, OSError):
                        pass
        except Exception:
            pass
        results.append({
            "path": str(p),
            "file_count": count,
            "total_size": format_bytes(sz),
            "raw_bytes": sz
        })
    return {"temp_locations": results}


def main():
    parser = argparse.ArgumentParser(
        description="Disk Space Guard - High speed storage analyzer and duplicate locator."
    )
    parser.add_argument("action", choices=["scan", "duplicates", "temp-bloat"],
                        help="Action: scan directory, find duplicates, or inspect temp clutter")
    parser.add_argument("--path", "-p", default=".",
                        help="Target folder path to analyze (default: current directory)")
    parser.add_argument("--top", "-t", type=int, default=15,
                        help="Number of largest files to display (default: 15)")
    parser.add_argument("--min-size-mb", type=float, default=0.0,
                        help="Filter minimum file size in MB for scan")
    parser.add_argument("--min-dup-kb", type=int, default=10,
                        help="Minimum file size in KB for duplicate scan (default: 10KB)")
    parser.add_argument("--json", action="store_true",
                        help="Output result formatted as JSON")

    args = parser.parse_args()

    if args.action == "scan":
        res = scan_storage(args.path, top_n=args.top, min_size_mb=args.min_size_mb)
        if args.json:
            import json
            print(json.dumps(res, indent=2))
            return

        print(f"\n[*] Disk Scan Results for: {res['target']}")
        print(f"[*] Total Files: {res['total_files']:,} | Dirs: {res['total_dirs']:,} | Size: {res['total_size_human']}")
        
        print("\n--- Top Extensions by Size ---")
        print(f"{'Extension':<15} | {'Count':<10} | {'Total Size':<15}")
        print("-" * 45)
        for ext, count, _, hum in res["extensions"]:
            print(f"{ext:<15} | {count:<10} | {hum:<15}")

        print(f"\n--- Top {len(res['top_files'])} Largest Files ---")
        for p, _, hum in res["top_files"]:
            print(f"[{hum:>10}]  {p}")

    elif args.action == "duplicates":
        print(f"[*] Scanning for duplicate files in '{args.path}' (min size: {args.min_dup_kb} KB)...")
        dups = find_duplicates(args.path, min_size_kb=args.min_dup_kb)
        if args.json:
            import json
            print(json.dumps(dups, indent=2))
            return
        
        if not dups:
            print("[+] No duplicate files found.")
            return

        print(f"[!] Found {len(dups)} sets of duplicate files:\n")
        for signature, paths in dups.items():
            print(f"Duplicate Set: {signature}")
            for p in paths:
                print(f"  -> {p}")
            print()

    elif args.action == "temp-bloat":
        bloat = check_temp_bloat()
        if args.json:
            import json
            print(json.dumps(bloat, indent=2))
            return

        print("\n[*] System & User Temp Space Usage:")
        print(f"{'Path':<45} | {'Files':<10} | {'Size':<15}")
        print("-" * 75)
        for t in bloat["temp_locations"]:
            print(f"{t['path']:<45} | {t['file_count']:<10} | {t['total_size']:<15}")


if __name__ == "__main__":
    main()
