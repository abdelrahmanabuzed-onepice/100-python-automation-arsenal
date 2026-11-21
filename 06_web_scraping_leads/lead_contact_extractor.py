#!/usr/bin/env python3
"""
High-Speed Web Lead & Contact Extractor
=======================================
Crawls target websites and landing pages to harvest business contact intelligence:
- Extracts emails (filtered against media file false-positives)
- Captures international phone numbers
- Discovers social handles (LinkedIn, Twitter/X, GitHub, Facebook, Instagram)
- Multi-threaded crawling with JSON and CSV export

Keywords: lead generation, web scraper, email harvester, contact extraction, osint
"""

import sys
import re
import csv
import json
import argparse
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Set, Dict, List, Optional, Any

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    requests = None
    BeautifulSoup = None

# Regex patterns
EMAIL_REGEX = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
PHONE_REGEX = re.compile(r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}')

SOCIAL_DOMAINS = {
    "linkedin": re.compile(r'https?://(?:www\.)?linkedin\.com/(?:company|in)/[A-Za-z0-9_-]+'),
    "twitter": re.compile(r'https?://(?:www\.)?(?:twitter\.com|x\.com)/[A-Za-z0-9_]+'),
    "github": re.compile(r'https?://(?:www\.)?github\.com/[A-Za-z0-9_-]+'),
    "facebook": re.compile(r'https?://(?:www\.)?facebook\.com/[A-Za-z0-9_.-]+'),
    "instagram": re.compile(r'https?://(?:www\.)?instagram\.com/[A-Za-z0-9_.-]+')
}

IGNORE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.css', '.js')


def clean_emails(raw_emails: List[str]) -> Set[str]:
    """Filter out media extensions and garbage matches."""
    cleaned = set()
    for e in raw_emails:
        e_lower = e.lower().strip()
        if not any(e_lower.endswith(ext) for ext in IGNORE_EXTENSIONS):
            # Eliminate trivial dummy addresses
            if not any(dummy in e_lower for dummy in ('example.com', 'w3.org', 'schema.org', 'test.com')):
                cleaned.add(e)
    return cleaned


def scrape_page_leads(url: str, timeout: float = 8.0) -> Dict[str, Any]:
    """Scrape contact info and social links from a single URL."""
    if not requests or not BeautifulSoup:
        raise ImportError("requests and beautifulsoup4 are required for web scraping.")

    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    }

    result = {
        "url": url,
        "title": "",
        "status": 0,
        "emails": [],
        "phones": [],
        "socials": {},
        "internal_links": []
    }

    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
        result["status"] = resp.status_code
        if resp.status_code != 200:
            return result

        html = resp.text
        soup = BeautifulSoup(html, 'html.parser')
        result["title"] = soup.title.string.strip() if soup.title and soup.title.string else ""

        # Extract Emails
        found_emails = EMAIL_REGEX.findall(html)
        result["emails"] = sorted(list(clean_emails(found_emails)))

        # Extract Phones
        found_phones = PHONE_REGEX.findall(html)
        # Filter short noise
        valid_phones = set()
        for p in found_phones:
            p_strip = p.strip()
            digits = re.sub(r'\D', '', p_strip)
            if 10 <= len(digits) <= 15:
                valid_phones.add(p_strip)
        result["phones"] = sorted(list(valid_phones))

        # Extract Socials
        socials_map = {}
        for platform, pattern in SOCIAL_DOMAINS.items():
            matches = pattern.findall(html)
            if matches:
                socials_map[platform] = sorted(list(set(matches)))
        result["socials"] = socials_map

        # Discover internal links for optional crawling
        base_netloc = urlparse(url).netloc
        links = set()
        for a in soup.find_all('a', href=True):
            href = a['href'].strip()
            full_url = urljoin(url, href)
            if urlparse(full_url).netloc == base_netloc and not full_url.endswith(IGNORE_EXTENSIONS):
                links.add(full_url.split('#')[0])
        result["internal_links"] = list(links)[:25]

    except Exception as e:
        result["error"] = str(e)

    return result


def run_crawler(start_urls: List[str], max_depth: int = 1, threads: int = 5) -> List[Dict[str, Any]]:
    """Crawl initial URLs and extract contact intelligence."""
    visited = set()
    to_visit = set(start_urls)
    results = []

    for depth in range(max_depth):
        if not to_visit:
            break
        current_batch = list(to_visit)
        to_visit = set()

        with ThreadPoolExecutor(max_workers=threads) as executor:
            future_to_url = {executor.submit(scrape_page_leads, u): u for u in current_batch if u not in visited}
            for future in as_completed(future_to_url):
                u = future_to_url[future]
                visited.add(u)
                try:
                    res = future.result()
                    results.append(res)
                    if depth + 1 < max_depth:
                        for internal_link in res.get("internal_links", []):
                            if internal_link not in visited:
                                to_visit.add(internal_link)
                except Exception:
                    pass

    return results


def main():
    parser = argparse.ArgumentParser(
        description="High-Speed Web Lead & Contact Extractor"
    )
    parser.add_argument("urls", nargs="+", help="One or more seed URLs to extract leads from")
    parser.add_argument("--depth", "-d", type=int, default=1,
                        help="Crawl depth (1 = seed URLs only, 2 = follow internal links)")
    parser.add_argument("--threads", "-t", type=int, default=5,
                        help="Crawler thread concurrency (default: 5)")
    parser.add_argument("--output", "-o", default=None,
                        help="Export results to CSV or JSON file")
    parser.add_argument("--json", action="store_true",
                        help="Print output formatted as JSON")

    args = parser.parse_args()

    print(f"[*] Crawling {len(args.urls)} target(s) at depth {args.depth}...")
    records = run_crawler(args.urls, max_depth=args.depth, threads=args.threads)

    if args.json:
        print(json.dumps(records, indent=2))
        return

    print("\n" + "=" * 70)
    print(f"Discovered Lead Intelligence ({len(records)} page(s) analyzed):")
    print("=" * 70)

    for item in records:
        print(f"\n[URL]   : {item['url']}")
        if item.get("error"):
            print(f"[Status]: [ERROR] {item['error']}")
        elif item.get("status") and item.get("status") != 200:
            print(f"[Status]: HTTP {item['status']}")
        print(f"[Title] : {item.get('title', 'N/A')}")
        emails_str = ", ".join(item.get("emails", [])) or "None"
        phones_str = ", ".join(item.get("phones", [])) or "None"
        print(f"[Emails]: {emails_str}")
        print(f"[Phones]: {phones_str}")
        socials = item.get("socials", {})
        if socials:
            print("[Social Profiles]:")
            for plat, links in socials.items():
                print(f"  - {plat.capitalize()}: {', '.join(links)}")

    if args.output:
        out_p = Path(args.output)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        if out_p.suffix.lower() == ".json":
            with open(out_p, "w", encoding="utf-8") as f:
                json.dump(records, f, indent=2)
            print(f"\n[+] Saved results to {args.output}")
        else:
            with open(out_p, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["URL", "Title", "Emails", "Phones", "Socials"])
                for it in records:
                    soc_flat = " | ".join([f"{k}: {', '.join(v)}" for k, v in it.get("socials", {}).items()])
                    writer.writerow([
                        it["url"],
                        it.get("title", ""),
                        "; ".join(it.get("emails", [])),
                        "; ".join(it.get("phones", [])),
                        soc_flat
                    ])
            print(f"\n[+] Saved CSV export to {args.output}")


if __name__ == "__main__":
    main()
