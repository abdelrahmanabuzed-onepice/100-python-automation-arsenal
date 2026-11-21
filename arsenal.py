#!/usr/bin/env python3
"""
100 Python Automation Arsenal - Master Command Center
=====================================================
Unified interactive launcher and CLI dispatch for the entire automation suite.

Usage:
  python arsenal.py                 # Launch interactive TUI menu
  python arsenal.py list            # List all tools and categories
  python arsenal.py run <tool> ...  # Directly run any tool by ID or name
  python arsenal.py search <query>  # Search tools by keyword or tags
  python arsenal.py test-all        # Verify health of all tools across suite
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Any

# Root folder of repository
BASE_DIR = Path(__file__).resolve().parent

# ANSI Color Codes
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

# Registry of all tools in the arsenal
TOOLS_REGISTRY = [
    # 01 Windows Sysadmin
    {
        "id": "1",
        "category": "01_windows_sysadmin",
        "name": "Windows Service Watchdog",
        "file": "01_windows_sysadmin/service_watchdog.py",
        "description": "Monitors Windows services & processes, detects crashes, auto-heals / restarts.",
        "keywords": ["windows", "sysadmin", "service", "watchdog", "process", "auto-restart"]
    },
    {
        "id": "2",
        "category": "01_windows_sysadmin",
        "name": "Disk Space Guard & Clutter Analyzer",
        "file": "01_windows_sysadmin/disk_space_guard.py",
        "description": "Locates storage hogs, analyzes extension footprints, and detects duplicate files.",
        "keywords": ["disk", "storage", "cleanup", "duplicates", "temp", "sysadmin"]
    },

    # 02 Cybersecurity Recon
    {
        "id": "3",
        "category": "02_cybersecurity_recon",
        "name": "Port Vulnerability Scanner",
        "file": "02_cybersecurity_recon/port_vulnerability_scanner.py",
        "description": "Multi-threaded TCP port scanner with banner grabbing and latency profiling.",
        "keywords": ["port scanner", "cybersecurity", "recon", "banner grabber", "infosec"]
    },
    {
        "id": "4",
        "category": "02_cybersecurity_recon",
        "name": "Subdomain & DNS Enumerator",
        "file": "02_cybersecurity_recon/subdomain_dns_enum.py",
        "description": "Discovers active subdomains, queries A/MX/TXT/NS records, and audits DNS attack surface.",
        "keywords": ["subdomain", "dns", "recon", "osint", "enumeration", "security"]
    },

    # 03 Network Protocols
    {
        "id": "5",
        "category": "03_network_protocols",
        "name": "SMTP Deliverability Checker",
        "file": "03_network_protocols/smtp_deliverability_checker.py",
        "description": "Validates MX records, performs live SMTP handshake, tests recipient acceptance & SPF/DMARC.",
        "keywords": ["smtp", "email deliverability", "mx", "spf", "dmarc", "handshake"]
    },
    {
        "id": "6",
        "category": "03_network_protocols",
        "name": "HTTP Latency & SSL Monitor",
        "file": "03_network_protocols/http_latency_monitor.py",
        "description": "Profiles DNS, TCP, TLS, TTFB milestones and audits SSL certificate expiration.",
        "keywords": ["http", "latency", "ttfb", "ssl", "certificate", "uptime", "sla"]
    },

    # 04 Data Office Automation
    {
        "id": "7",
        "category": "04_data_office_automation",
        "name": "CSV & Excel Deduplicator",
        "file": "04_data_office_automation/csv_excel_deduper_transformer.py",
        "description": "High-throughput data cleaner, phone/email normalizer, and duplicate row eliminator.",
        "keywords": ["csv", "excel", "deduplication", "cleaner", "pipeline", "office"]
    },
    {
        "id": "8",
        "category": "04_data_office_automation",
        "name": "JSON Schema Validator & Auto-Repair",
        "file": "04_data_office_automation/json_schema_validator_formatter.py",
        "description": "Validates JSON structure against schemas, minifies, beautifies, and fixes malformed JSON syntax.",
        "keywords": ["json", "validator", "repair", "formatter", "linter", "schema"]
    },

    # 05 PDF Document Tools
    {
        "id": "9",
        "category": "05_pdf_document_tools",
        "name": "PDF Merger & Splitter",
        "file": "05_pdf_document_tools/pdf_merge_splitter.py",
        "description": "Merges multiple PDF files, slices custom page ranges, and rotates documents offline.",
        "keywords": ["pdf", "merger", "splitter", "page extractor", "office", "documents"]
    },
    {
        "id": "10",
        "category": "05_pdf_document_tools",
        "name": "PDF Metadata Scrubber",
        "file": "05_pdf_document_tools/pdf_metadata_scrubber.py",
        "description": "Audits and purges hidden metadata, author footprints, and printer tags from PDFs.",
        "keywords": ["pdf", "metadata", "privacy", "scrubber", "anonymize", "security"]
    },

    # 06 Web Scraping Leads
    {
        "id": "11",
        "category": "06_web_scraping_leads",
        "name": "Web Lead & Contact Extractor",
        "file": "06_web_scraping_leads/lead_contact_extractor.py",
        "description": "Crawls web pages to extract clean business emails, phone numbers, and social media handles.",
        "keywords": ["scraper", "leads", "email extractor", "phone", "osint", "growth"]
    },
    {
        "id": "12",
        "category": "06_web_scraping_leads",
        "name": "On-Page SEO & Meta Auditor",
        "file": "06_web_scraping_leads/meta_seo_auditor.py",
        "description": "Audits meta titles, descriptions, canonicals, H1 hierarchy, OpenGraph, and computes SEO score.",
        "keywords": ["seo", "audit", "opengraph", "headings", "meta tags", "web"]
    },

    # 07 Local AI Utilities
    {
        "id": "13",
        "category": "07_local_ai_utilities",
        "name": "Local LLM & Ollama Benchmarker",
        "file": "07_local_ai_utilities/ollama_model_benchmarker.py",
        "description": "Measures Ollama token generation rate (tok/s), latency, and multi-prompt performance.",
        "keywords": ["ollama", "local ai", "benchmark", "llm", "tokens per second", "vram"]
    },
    {
        "id": "14",
        "category": "07_local_ai_utilities",
        "name": "Smart Prompt & Spintax Generator",
        "file": "07_local_ai_utilities/smart_prompt_spintax_generator.py",
        "description": "Generates high-entropy polymorphic prompt/email variations with Jaccard uniqueness scoring.",
        "keywords": ["spintax", "polymorphic", "prompt engineering", "permutations", "ai"]
    },

    # 08 File Storage Systems
    {
        "id": "15",
        "category": "08_file_storage_systems",
        "name": "Directory Hash Manifest & Verifier",
        "file": "08_file_storage_systems/hash_integrity_verifier.py",
        "description": "Builds cryptographic SHA256 baselines and detects modified, missing, or added files.",
        "keywords": ["hash", "integrity", "sha256", "manifest", "backup", "verification"]
    },
    {
        "id": "16",
        "category": "08_file_storage_systems",
        "name": "Smart Rule-Based File Organizer",
        "file": "08_file_storage_systems/smart_file_organizer.py",
        "description": "Cleans downloads and messy directories by auto-sorting into classified taxonomy folders.",
        "keywords": ["organizer", "file sorter", "tidy", "downloads", "storage", "automation"]
    },

    # 09 Developer Productivity
    {
        "id": "17",
        "category": "09_developer_productivity",
        "name": "Git Activity & Velocity Analyzer",
        "file": "09_developer_productivity/git_repo_activity_analyzer.py",
        "description": "Analyzes Git repository commit velocity, top authors, file churn hotspots, and commit curves.",
        "keywords": ["git", "velocity", "developer productivity", "code churn", "analytics"]
    },
    {
        "id": "18",
        "category": "09_developer_productivity",
        "name": "Env Config Generator & Leak Auditor",
        "file": "09_developer_productivity/env_config_generator_vault.py",
        "description": "Generates .env.example templates from codebase, detects secret leaks, and outputs secure keys.",
        "keywords": ["env", "secrets", "api keys", "auditor", "generator", "security"]
    },

    # 10 Media Image Processing
    {
        "id": "19",
        "category": "10_media_image_processing",
        "name": "Batch Image Compressor & WebP Converter",
        "file": "10_media_image_processing/batch_image_optimizer.py",
        "description": "Batch compresses JPG/PNG files and converts to next-gen WebP with 60-80% file size reduction.",
        "keywords": ["image compression", "webp", "batch resize", "media", "performance"]
    },
    {
        "id": "20",
        "category": "10_media_image_processing",
        "name": "Image EXIF Privacy Sanitizer",
        "file": "10_media_image_processing/image_exif_sanitizer.py",
        "description": "Audits and purges GPS coordinates, camera model signatures, and timestamps from images.",
        "keywords": ["exif", "geotag", "gps", "privacy", "sanitizer", "image metadata"]
    }
]


def print_banner():
    banner = f"""{CYAN}{BOLD}
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║            ⚡  100 PYTHON AUTOMATION ARSENAL : MASTER CLI  ⚡             ║
║           Industrial-Grade Standalone Utilities & Automation Suite        ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝{RESET}"""
    print(banner)


def find_tool(identifier: str) -> Optional[Dict[str, Any]]:
    """Look up a tool by ID or by filename substring."""
    clean_id = identifier.strip().lower()
    for t in TOOLS_REGISTRY:
        if t["id"] == clean_id:
            return t
        stem = Path(t["file"]).stem.lower()
        if clean_id == stem or clean_id in t["name"].lower() or clean_id == t["file"].lower():
            return t
    return None


def execute_tool(tool_info: Dict[str, Any], args: List[str]):
    """Run tool with python interpreter."""
    target_path = BASE_DIR / tool_info["file"]
    if not target_path.exists():
        print(f"{RED}[!] Error: Target script does not exist at {target_path}{RESET}", file=sys.stderr)
        return

    cmd = [sys.executable, str(target_path)] + args
    print(f"\n{GREEN}[*] Launching: {tool_info['name']}{RESET}", flush=True)
    print(f"{DIM}[Command] {' '.join(cmd)}{RESET}\n", flush=True)
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}[*] Tool execution interrupted by user.{RESET}")


def list_tools(category_filter: Optional[str] = None):
    """Print tabular inventory of tools."""
    current_cat = None
    print(f"\n{BOLD}{'ID':<4} | {'Tool Name':<38} | {'File / Script':<38}{RESET}")
    print("=" * 86)

    for t in TOOLS_REGISTRY:
        if category_filter and category_filter.lower() not in t["category"].lower():
            continue

        if t["category"] != current_cat:
            current_cat = t["category"]
            print(f"\n{CYAN}{BOLD}📂 [{current_cat}]{RESET}")

        print(f"{GREEN}{t['id']:<4}{RESET} | {BOLD}{t['name']:<38}{RESET} | {DIM}{t['file']:<38}{RESET}")
        print(f"     └─ {t['description']}")
    print()


def search_tools(query: str):
    """Search registry by query string."""
    q = query.lower()
    matches = []
    for t in TOOLS_REGISTRY:
        if (q in t["name"].lower() or
            q in t["description"].lower() or
            q in t["category"].lower() or
            any(q in k.lower() for k in t["keywords"])):
            matches.append(t)

    print(f"\n{BOLD}Search Results for '{query}' ({len(matches)} tool(s) found):{RESET}")
    print("=" * 75)
    for m in matches:
        print(f"{GREEN}[#{m['id']}]{RESET} {BOLD}{m['name']}{RESET} ({CYAN}{m['category']}{RESET})")
        print(f"   {m['description']}")
        print(f"   {DIM}Tags: {', '.join(m['keywords'])}{RESET}\n")


def test_suite_health():
    """Verify that all 20 tools execute clean --help without errors."""
    print(f"\n{BOLD}[*] Running System Diagnostic Gate on all {len(TOOLS_REGISTRY)} tools...{RESET}\n")
    passed = 0
    failed = 0

    print(f"{'ID':<4} | {'Tool Script':<50} | {'Status'}")
    print("-" * 70)

    for t in TOOLS_REGISTRY:
        target = BASE_DIR / t["file"]
        if not target.exists():
            print(f"{t['id']:<4} | {t['file']:<50} | {RED}MISSING FILE{RESET}")
            failed += 1
            continue

        res = subprocess.run([sys.executable, str(target), "--help"], capture_output=True, text=True)
        if res.returncode == 0:
            print(f"{GREEN}{t['id']:<4}{RESET} | {t['file']:<50} | {GREEN}[PASS: 200 OK]{RESET}")
            passed += 1
        else:
            print(f"{RED}{t['id']:<4}{RESET} | {t['file']:<50} | {RED}[FAIL: Error {res.returncode}]{RESET}")
            failed += 1

    print("\n" + "=" * 70)
    print(f"Suite Health Check: {GREEN}{passed} Passed{RESET}, {RED}{failed} Failed{RESET} out of {len(TOOLS_REGISTRY)} Tools.")
    print("=" * 70)


def interactive_menu():
    """Run interactive terminal TUI menu."""
    while True:
        print_banner()
        print(f"{BOLD}Main Menu:{RESET}")
        print(f"  {GREEN}[1]{RESET} List all tools by category")
        print(f"  {GREEN}[2]{RESET} Search tools by keyword or domain")
        print(f"  {GREEN}[3]{RESET} Run a tool by ID or name")
        print(f"  {GREEN}[4]{RESET} Test all tools (--help health audit)")
        print(f"  {RED}[0]{RESET} Exit")

        try:
            choice = input(f"\n{BOLD}Select an option [0-4]: {RESET}").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n[*] Exiting Arsenal.")
            break

        if choice == "0":
            print("[*] Goodbye!")
            break
        elif choice == "1":
            list_tools()
            input(f"{DIM}Press Enter to return to menu...{RESET}")
        elif choice == "2":
            q = input(f"{BOLD}Enter search keyword: {RESET}").strip()
            if q:
                search_tools(q)
            input(f"{DIM}Press Enter to return to menu...{RESET}")
        elif choice == "3":
            t_id = input(f"{BOLD}Enter Tool ID or name: {RESET}").strip()
            tool = find_tool(t_id)
            if not tool:
                print(f"{RED}[!] No tool matched '{t_id}'.{RESET}")
                input(f"{DIM}Press Enter to return to menu...{RESET}")
                continue

            print(f"\nSelected: {BOLD}{tool['name']}{RESET} ({tool['file']})")
            args_input = input(f"{BOLD}Enter CLI arguments (or leave blank for --help): {RESET}").strip()
            args = args_input.split() if args_input else ["--help"]
            execute_tool(tool, args)
            input(f"\n{DIM}Execution complete. Press Enter to return to menu...{RESET}")
        elif choice == "4":
            test_suite_health()
            input(f"{DIM}Press Enter to return to menu...{RESET}")


def main():
    parser = argparse.ArgumentParser(
        description="100 Python Automation Arsenal - Master Command Center",
        add_help=False
    )
    parser.add_argument("command", nargs="?", default=None,
                        choices=["list", "run", "search", "test-all", "help"],
                        help="Action to perform")
    parser.add_argument("target", nargs="?", default=None,
                        help="Target tool ID/name or search term")
    parser.add_argument("extra_args", nargs=argparse.REMAINDER,
                        help="Arguments passed directly to target tool")

    args = parser.parse_args()

    if not args.command:
        interactive_menu()
        return

    if args.command == "help":
        print(__doc__)
        return

    if args.command == "list":
        list_tools(args.target)
    elif args.command == "search":
        if not args.target:
            print("[!] Please provide a search term: python arsenal.py search <keyword>")
            return
        search_tools(args.target)
    elif args.command == "run":
        if not args.target:
            print("[!] Please specify a tool: python arsenal.py run <tool_id_or_name> [args...]")
            return
        tool = find_tool(args.target)
        if not tool:
            print(f"[!] Tool '{args.target}' not found in registry. Use 'python arsenal.py list' to view available tools.")
            sys.exit(1)
        execute_tool(tool, args.extra_args or ["--help"])
    elif args.command == "test-all":
        test_suite_health()


if __name__ == "__main__":
    main()
