#!/usr/bin/env python3
"""
Git Repository Activity & Velocity Analyzer
===========================================
Deep Git analytics, developer velocity, churn hotspots, and commit temporal trends:
- Top contributors and author impact metrics
- File churn hotspots (identifies files with highest bug/change volatility)
- Hourly and day-of-week commit velocity breakdown with ASCII charts
- 100% offline using standard Git porcelain

Keywords: git analytics, git velocity, developer productivity, code churn, repository metrics
"""

import sys
import subprocess
import json
import argparse
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime
from typing import Dict, List, Optional, Any


def run_git_command(args: List[str], repo_path: str) -> str:
    """Execute git command and return stripped stdout."""
    res = subprocess.run(
        ["git"] + args,
        cwd=repo_path,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False
    )
    if res.returncode != 0:
        raise RuntimeError(f"Git command failed: {res.stderr.strip()}")
    return res.stdout


def analyze_git_repo(repo_path: str, max_commits: int = 1000) -> Dict[str, Any]:
    """Parse git commit log to extract analytics."""
    p = Path(repo_path).resolve()
    if not (p / ".git").exists():
        raise FileNotFoundError(f"Not a git repository: {repo_path}")

    # Format: %H|%an|%ae|%at|%ad
    log_raw = run_git_command([
        "log",
        f"-n{max_commits}",
        "--format=%H|%an|%ae|%at|%ad",
        "--date=iso-strict"
    ], str(p))

    if not log_raw.strip():
        return {"error": "Repository has no commits yet."}

    lines = log_raw.strip().splitlines()
    total_commits = len(lines)

    authors_counter = Counter()
    weekday_counter = Counter()
    hour_counter = Counter()
    timestamps = []

    for line in lines:
        parts = line.split("|")
        if len(parts) >= 5:
            author = parts[1].strip()
            date_str = parts[4].strip()
            authors_counter[author] += 1
            try:
                dt = datetime.fromisoformat(date_str)
                weekday_counter[dt.strftime("%a")] += 1
                hour_counter[dt.hour] += 1
                timestamps.append(dt)
            except Exception:
                pass

    # Churned files (top changed files)
    churn_raw = run_git_command([
        "log",
        f"-n{min(max_commits, 200)}",
        "--name-only",
        "--format="
    ], str(p))

    churn_counter = Counter()
    for f in churn_raw.splitlines():
        f = f.strip()
        if f:
            churn_counter[f] += 1

    top_authors = [
        {"author": a, "commits": c, "share_pct": round((c / total_commits) * 100, 1)}
        for a, c in authors_counter.most_common(10)
    ]

    hotspots = [
        {"file": f, "modifications": c}
        for f, c in churn_counter.most_common(10)
    ]

    days_order = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    weekday_stats = {d: weekday_counter[d] for d in days_order}

    return {
        "repo": str(p),
        "analyzed_commits": total_commits,
        "unique_authors": len(authors_counter),
        "first_commit": min(timestamps).isoformat() if timestamps else None,
        "latest_commit": max(timestamps).isoformat() if timestamps else None,
        "top_authors": top_authors,
        "hotspots": hotspots,
        "by_weekday": weekday_stats,
        "by_hour": dict(sorted(hour_counter.items()))
    }


def render_ascii_bar(val: int, max_val: int, width: int = 30) -> str:
    """Render a text bar."""
    if max_val <= 0:
        return ""
    length = int((val / max_val) * width)
    return "█" * length + "░" * (width - length)


def main():
    parser = argparse.ArgumentParser(
        description="Git Repository Activity & Velocity Analyzer"
    )
    parser.add_argument("repo", nargs="?", default=".",
                        help="Path to Git repository (default: current directory)")
    parser.add_argument("--limit", "-n", type=int, default=1000,
                        help="Maximum number of commits to analyze (default: 1000)")
    parser.add_argument("--json", action="store_true",
                        help="Output analysis in JSON format")

    args = parser.parse_args()

    try:
        report = analyze_git_repo(args.repo, max_commits=args.limit)
    except Exception as e:
        print(f"[!] Error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(json.dumps(report, indent=2))
        return

    if "error" in report:
        print(f"[!] {report['error']}")
        return

    print("\n" + "=" * 70)
    print(f"Git Velocity & Intelligence Report: {Path(report['repo']).name}")
    print("=" * 70)
    print(f"  Total Commits Analyzed : {report['analyzed_commits']:,}")
    print(f"  Unique Contributors    : {report['unique_authors']}")
    print(f"  Activity Span          : {report['first_commit'][:10]} -> {report['latest_commit'][:10]}")

    print("\n--- Top Contributors ---")
    print(f"{'Author':<28} | {'Commits':<8} | {'Impact'}")
    print("-" * 55)
    for a in report["top_authors"]:
        print(f"{a['author']:<28} | {a['commits']:<8} | {a['share_pct']}%")

    print("\n--- Code Churn Hotspots (Most Frequently Modified) ---")
    for h in report["hotspots"][:7]:
        print(f"  [{h['modifications']:>3} edits]  {h['file']}")

    print("\n--- Day-of-Week Commit Distribution ---")
    max_day = max(report["by_weekday"].values()) if report["by_weekday"].values() else 1
    for day, count in report["by_weekday"].items():
        bar = render_ascii_bar(count, max_day, width=25)
        print(f"  {day:<4} | {bar} {count:>3}")


if __name__ == "__main__":
    main()
