#!/usr/bin/env python3
"""
Subdomain & DNS Reconnaissance Enumerator
=========================================
Discover active subdomains, map DNS attack surface, and query comprehensive DNS records.

Keywords: subdomain enumeration, DNS recon, OSINT, cybersecurity, domain reconnaissance
"""

import sys
import socket
import json
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional, Any

try:
    import dns.resolver
    HAS_DNSPYTHON = True
except ImportError:
    HAS_DNSPYTHON = False

DEFAULT_WORDLIST = [
    "www", "mail", "remote", "blog", "webmail", "server", "ns1", "ns2",
    "smtp", "secure", "vpn", "api", "dev", "staging", "test", "portal",
    "admin", "app", "auth", "m", "support", "billing", "shop", "git",
    "cpanel", "whm", "cloud", "direct", "beta", "status", "docs", "login",
    "dashboard", "cdn", "mx", "gateway", "office", "internal", "relay"
]


def get_configured_resolver() -> Any:
    """Create a DNS resolver with fallback public nameservers for reliability."""
    if not HAS_DNSPYTHON:
        return None
    r = dns.resolver.Resolver()
    # Use reliable, low-latency public DNS resolvers
    r.nameservers = ['8.8.8.8', '1.1.1.1', '8.8.4.4']
    r.timeout = 1.5
    r.lifetime = 2.0
    return r


def query_root_dns_records(domain: str) -> Dict[str, List[str]]:
    """Query standard DNS records (A, MX, TXT, NS) for the root domain."""
    records: Dict[str, List[str]] = {
        "A": [],
        "AAAA": [],
        "MX": [],
        "TXT": [],
        "NS": []
    }
    
    resolver = get_configured_resolver()
    if resolver:
        for rtype in records.keys():
            try:
                answers = resolver.resolve(domain, rtype)
                records[rtype] = [str(r.to_text()).strip('"') for r in answers]
            except Exception:
                pass
    
    if not records["A"]:
        try:
            ips = socket.gethostbyname_ex(domain)[2]
            records["A"] = ips
        except Exception:
            pass

    return records


def resolve_subdomain(subdomain: str, root_domain: str, resolver: Any = None) -> Optional[Dict[str, Any]]:
    """Resolve a specific subdomain candidate."""
    fqdn = f"{subdomain}.{root_domain}"
    if resolver:
        try:
            answers = resolver.resolve(fqdn, "A")
            ips = [r.to_text() for r in answers]
            if ips:
                return {"subdomain": subdomain, "fqdn": fqdn, "ips": ips, "status": "ACTIVE"}
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
            return None
        except Exception:
            pass
    else:
        # Fallback to standard socket only when dnspython is unavailable
        try:
            ips = socket.gethostbyname_ex(fqdn)[2]
            if ips:
                return {"subdomain": subdomain, "fqdn": fqdn, "ips": ips, "status": "ACTIVE"}
        except Exception:
            pass

    return None


def run_enumeration(domain: str, wordlist: List[str], threads: int = 40) -> Dict[str, Any]:
    """Run concurrent subdomain discovery against the wordlist."""
    clean_domain = domain.strip().lower()
    if clean_domain.startswith("http://"):
        clean_domain = clean_domain[7:]
    elif clean_domain.startswith("https://"):
        clean_domain = clean_domain[8:]
    clean_domain = clean_domain.split("/")[0]

    dns_records = query_root_dns_records(clean_domain)
    active_subdomains: List[Dict[str, Any]] = []
    resolver = get_configured_resolver()

    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = {executor.submit(resolve_subdomain, sub.strip(), clean_domain, resolver): sub for sub in wordlist}
        for future in as_completed(futures):
            res = future.result()
            if res:
                active_subdomains.append(res)

    active_subdomains.sort(key=lambda x: x["fqdn"])

    return {
        "domain": clean_domain,
        "root_dns_records": dns_records,
        "scanned_candidates": len(wordlist),
        "found_subdomains_count": len(active_subdomains),
        "subdomains": active_subdomains
    }


def main():
    parser = argparse.ArgumentParser(
        description="Subdomain & DNS Reconnaissance Enumerator"
    )
    parser.add_argument("domain", help="Target root domain (e.g. example.com)")
    parser.add_argument("--wordlist", "-w", type=str, default=None,
                        help="Path to custom subdomain wordlist file (one per line)")
    parser.add_argument("--threads", "-t", type=int, default=30,
                        help="Number of DNS resolution threads (default: 30)")
    parser.add_argument("--json", action="store_true",
                        help="Output results as JSON")

    args = parser.parse_args()

    wordlist = DEFAULT_WORDLIST
    if args.wordlist:
        try:
            with open(args.wordlist, "r", encoding="utf-8") as f:
                wordlist = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        except Exception as e:
            print(f"[!] Error loading wordlist: {e}", file=sys.stderr)
            sys.exit(1)

    print(f"[*] Enumerating subdomains for '{args.domain}' ({len(wordlist)} candidates)...")
    data = run_enumeration(args.domain, wordlist, threads=args.threads)

    if args.json:
        print(json.dumps(data, indent=2))
        return

    print("\n=== Root Domain DNS Records ===")
    for rtype, vals in data["root_dns_records"].items():
        if vals:
            print(f"  [{rtype:<5}] {', '.join(vals[:4])}{'...' if len(vals) > 4 else ''}")

    print(f"\n=== Discovered Subdomains ({data['found_subdomains_count']}) ===")
    if not data["subdomains"]:
        print("  [-] No subdomains resolved from candidate list.")
    else:
        print(f"{'FQDN':<35} | {'Resolved IPs'}")
        print("-" * 65)
        for sub in data["subdomains"]:
            ips = ", ".join(sub["ips"][:3])
            print(f"{sub['fqdn']:<35} | {ips}")


if __name__ == "__main__":
    main()
