#!/usr/bin/env python3
"""
Environment Config Generator & Secret Leak Auditor
===================================================
Developer productivity and security suite:
- Scans codebase for accessed environment variables and compiles '.env.example'
- Audits repository for leaked API keys, tokens, passwords, and private certificates
- Cryptographic high-entropy secret generator for deployment configs

Keywords: env generator, secret leak scanner, api key auditor, devops config, security audit
"""

import os
import sys
import re
import secrets
import argparse
from pathlib import Path
from typing import Set, Dict, List, Tuple, Optional, Any

# Regex to detect env vars in Python, JS/TS, Go, etc.
ENV_VAR_PATTERNS = [
    re.compile(r'os\.(?:getenv|environ(?:\[|\.get\())\s*[\'"]([A-Z0-9_]{3,})[\'"]'),
    re.compile(r'process\.env\.([A-Z0-9_]{3,})'),
    re.compile(r'os\.Getenv\([\'"]([A-Z0-9_]{3,})[\'"]\)'),
    re.compile(r'env\([\'"]([A-Z0-9_]{3,})[\'"]\)')
]

# Regex patterns for accidental hardcoded secret leaks
LEAK_SIGNATURES = [
    ("AWS Access Key", re.compile(r'\b(AKIA[0-9A-Z]{16})\b')),
    ("OpenAI API Key", re.compile(r'\b(sk-[a-zA-Z0-9]{32,64})\b')),
    ("GitHub Personal Access Token", re.compile(r'\b(ghp_[a-zA-Z0-9]{36})\b')),
    ("Generic High-Entropy Secret", re.compile(r'(?i)(?:api[_-]?key|secret|password|auth_token)\s*[:=]\s*[\'"]([a-zA-Z0-9_\-\.]{20,})[\'"]')),
    ("Private Key Header", re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'))
]

IGNORED_DIRS = {".git", ".svn", "node_modules", "venv", ".venv", "__pycache__", "build", "dist"}


def scan_for_env_variables(repo_path: str) -> Set[str]:
    """Scan code files for environment variables accessed."""
    root = Path(repo_path).resolve()
    discovered_vars = set()

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRS]
        for fname in filenames:
            ext = Path(fname).suffix.lower()
            if ext in ('.py', '.js', '.ts', '.jsx', '.tsx', '.go', '.rs', '.php', '.rb', '.env'):
                fp = Path(dirpath) / fname
                try:
                    with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    for pat in ENV_VAR_PATTERNS:
                        matches = pat.findall(content)
                        for m in matches:
                            discovered_vars.add(m)
                except Exception:
                    continue

    return discovered_vars


def audit_for_secret_leaks(repo_path: str) -> List[Dict[str, Any]]:
    """Scan files for exposed credentials and API keys."""
    root = Path(repo_path).resolve()
    findings = []

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRS]
        for fname in filenames:
            if fname in ('.gitignore', 'requirements.txt'):
                continue
            fp = Path(dirpath) / fname
            try:
                with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_no, line in enumerate(f, 1):
                        for label, pat in LEAK_SIGNATURES:
                            m = pat.search(line)
                            if m:
                                matched_str = m.group(1) if m.groups() else m.group(0)
                                redacted = matched_str[:4] + "*" * (len(matched_str) - 8) + matched_str[-4:] if len(matched_str) > 10 else "***"
                                findings.append({
                                    "file": str(fp.relative_to(root)),
                                    "line": line_no,
                                    "type": label,
                                    "preview": redacted
                                })
            except Exception:
                continue

    return findings


def generate_cryptographic_secrets() -> Dict[str, str]:
    """Produce various high-entropy random secrets."""
    return {
        "hex_32_bytes": secrets.token_hex(32),
        "url_safe_token": secrets.token_urlsafe(32),
        "strong_password": "".join(secrets.choice("abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789!@#$%^&*") for _ in range(24))
    }


def main():
    parser = argparse.ArgumentParser(
        description="Environment Config Generator & Secret Leak Auditor"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Generate .env.example
    env_p = subparsers.add_parser("gen-example", help="Generate .env.example from codebase inspection")
    env_p.add_argument("path", nargs="?", default=".", help="Root codebase path to scan")
    env_p.add_argument("--output", "-o", default=".env.example", help="Output file path (default: .env.example)")

    # Audit secrets
    audit_p = subparsers.add_parser("audit-leaks", help="Audit repository for exposed secrets/keys")
    audit_p.add_argument("path", nargs="?", default=".", help="Target repository directory")
    audit_p.add_argument("--json", action="store_true", help="Output findings as JSON")

    # Generate secrets
    sec_p = subparsers.add_parser("gen-secret", help="Generate cryptographically secure random secrets")

    args = parser.parse_args()

    if args.command == "gen-example":
        print(f"[*] Scanning codebase at '{args.path}' for environment variable references...")
        vars_found = sorted(scan_for_env_variables(args.path))
        print(f"[+] Discovered {len(vars_found)} unique environment variable keys.")

        out_path = Path(args.output)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("# ===================================================================\n")
            f.write("# Environment Configuration Template (Generated Automatically)\n")
            f.write("# ===================================================================\n\n")
            for v in vars_found:
                f.write(f"{v}=\n")
        print(f"[+] Saved template -> {out_path}")

    elif args.command == "audit-leaks":
        print(f"[*] Auditing '{args.path}' for exposed credentials...")
        findings = audit_for_secret_leaks(args.path)

        if args.json:
            import json
            print(json.dumps(findings, indent=2))
            sys.exit(1 if findings else 0)

        if not findings:
            print("\n[+] Clean! No hardcoded credentials or API keys detected.")
        else:
            print(f"\n[!] WARNING: Detected {len(findings)} potential secret leak(s):")
            print(f"{'File':<35} | {'Line':<6} | {'Type':<25} | {'Redacted Match'}")
            print("-" * 80)
            for item in findings:
                print(f"{item['file']:<35} | {item['line']:<6} | {item['type']:<25} | {item['preview']}")
            sys.exit(1)

    elif args.command == "gen-secret":
        keys = generate_cryptographic_secrets()
        print("\n=== Cryptographically Secure Random Keys ===")
        print(f"  HEX 256-bit Key   : {keys['hex_32_bytes']}")
        print(f"  URL-Safe Token    : {keys['url_safe_token']}")
        print(f"  Complex Password  : {keys['strong_password']}")


if __name__ == "__main__":
    main()
