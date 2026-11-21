#!/usr/bin/env python3
"""
Smart Rule-Based File Organizer & Tidy-Up Engine
================================================
Organizes cluttered directories (Downloads, Desktop, Messy Folders) into structured taxonomies:
- Categorizes files by domain type (Documents, Images, Archives, Video, Audio, Code)
- Optional organization by creation/modification timeline (Year/Month)
- Non-destructive collision handling (auto-renames duplicates without overwriting)
- Full Dry-Run simulation mode with formatted preview table

Keywords: file organizer, auto sort, folder cleaner, sysadmin desktop organizer, file triage
"""

import os
import sys
import shutil
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

CATEGORY_MAP = {
    "Documents": [".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".xlsx", ".xls", ".csv", ".pptx", ".ppt", ".md", ".epub"],
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".tiff", ".ico", ".raw", ".psd"],
    "Video": [".mp4", ".mkv", ".mov", ".avi", ".flv", ".wmv", ".webm", ".m4v"],
    "Audio": [".mp3", ".wav", ".aac", ".flac", ".ogg", ".wma", ".m4a"],
    "Archives": [".zip", ".tar", ".gz", ".bz2", ".rar", ".7z", ".xz", ".iso"],
    "Code_Scripts": [".py", ".js", ".ts", ".html", ".css", ".json", ".xml", ".sh", ".bat", ".ps1", ".sql", ".rs", ".go", ".cpp", ".c", ".h", ".yaml", ".yml"],
    "Executables": [".exe", ".msi", ".dll", ".apk", ".appimage", ".dmg"]
}

IGNORED_NAMES = {".git", ".svn", ".vscode", ".idea", "node_modules", "arsenal.py"}


def get_unique_destination(dest_path: Path) -> Path:
    """If destination exists, append numeric counter (1), (2), etc."""
    if not dest_path.exists():
        return dest_path

    parent = dest_path.parent
    stem = dest_path.stem
    suffix = dest_path.suffix
    counter = 1

    while True:
        candidate = parent / f"{stem} ({counter}){suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def determine_category(ext: str) -> str:
    """Return category directory name based on file extension."""
    ext_lower = ext.lower()
    for cat, extensions in CATEGORY_MAP.items():
        if ext_lower in extensions:
            return cat
    return "Other"


def plan_or_execute_organize(
    target_dir: str,
    dry_run: bool = True,
    by_date: bool = False
) -> Dict[str, Any]:
    """Scan root of target folder and plan or move files into categories."""
    root = Path(target_dir).resolve()
    if not root.exists():
        raise FileNotFoundError(f"Target folder not found: {target_dir}")

    moves = []
    skipped = []

    for item in root.iterdir():
        if item.is_dir() or item.name in IGNORED_NAMES or item.name.startswith("."):
            continue

        ext = item.suffix
        category = determine_category(ext)

        if by_date:
            mtime = datetime.fromtimestamp(item.stat().st_mtime)
            dest_dir = root / category / mtime.strftime("%Y") / mtime.strftime("%m")
        else:
            dest_dir = root / category

        dest_file = dest_dir / item.name
        dest_file = get_unique_destination(dest_file)

        moves.append({
            "source": str(item),
            "filename": item.name,
            "category": category,
            "target": str(dest_file)
        })

    # Execute moves if not dry run
    if not dry_run:
        for m in moves:
            s = Path(m["source"])
            d = Path(m["target"])
            d.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(s, d)

    return {
        "target_dir": str(root),
        "dry_run": dry_run,
        "by_date": by_date,
        "total_files_planned": len(moves),
        "moves": moves
    }


def main():
    parser = argparse.ArgumentParser(
        description="Smart Rule-Based File Organizer & Tidy-Up Engine"
    )
    parser.add_argument("path", help="Folder to organize (e.g. ~/Downloads or C:/Temp)")
    parser.add_argument("--execute", action="store_true",
                        help="Perform actual file moving (Default is safe DRY-RUN)")
    parser.add_argument("--by-date", action="store_true",
                        help="Sub-categorize files by Year/Month")
    parser.add_argument("--json", action="store_true",
                        help="Output report formatted as JSON")

    args = parser.parse_args()
    is_dry_run = not args.execute

    res = plan_or_execute_organize(args.path, dry_run=is_dry_run, by_date=args.by_date)

    if args.json:
        import json
        print(json.dumps(res, indent=2))
        return

    mode_label = "[DRY-RUN SIMULATION]" if is_dry_run else "[EXECUTION COMPLETE]"
    print(f"\n=== Smart File Organizer {mode_label} ===")
    print(f"  Target Folder : {res['target_dir']}")
    print(f"  Files To Move : {res['total_files_planned']}")
    print(f"  Date Grouping : {res['by_date']}")

    if not res["moves"]:
        print("\n  [+] Target folder has no unorganized loose files.")
        return

    print("\n" + "=" * 70)
    print(f"{'File Name':<30} | {'Category':<15} | {'Destination'}")
    print("=" * 70)
    for m in res["moves"][:25]:
        p_name = Path(m["filename"]).name
        dest_rel = Path(m["target"]).relative_to(res["target_dir"])
        print(f"{p_name[:30]:<30} | {m['category']:<15} | {str(dest_rel)}")

    if len(res["moves"]) > 25:
        print(f"... and {len(res['moves']) - 25} more files.")

    if is_dry_run:
        print("\n[i] Notice: No files were touched. Run with '--execute' to perform movements.")


if __name__ == "__main__":
    main()
