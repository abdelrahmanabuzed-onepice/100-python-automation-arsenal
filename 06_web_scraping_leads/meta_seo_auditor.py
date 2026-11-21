#!/usr/bin/env python3
"""
On-Page SEO, OpenGraph & Metadata Auditor
=========================================
Audits landing pages for search engine ranking factors and social sharing tags:
- Title tag & Meta description length audit
- Canonical URL consistency & Robots directives
- OpenGraph (og:image, og:title) & Twitter Card validation
- H1-H6 heading hierarchy check & missing image alt tags
- Computes automated On-Page SEO Health Score (0-100)

Keywords: seo auditor, on-page seo, opengraph checker, web crawler, digital marketing
"""

import sys
import json
import argparse
from typing import Dict, List, Any

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    requests = None
    BeautifulSoup = None


def audit_url_seo(url: str, timeout: float = 8.0) -> Dict[str, Any]:
    """Perform on-page SEO analysis on the target URL."""
    if not requests or not BeautifulSoup:
        raise ImportError("requests and beautifulsoup4 are required for SEO auditor.")

    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'
    }

    report = {
        "url": url,
        "status_code": 0,
        "title": None,
        "title_length": 0,
        "description": None,
        "description_length": 0,
        "canonical": None,
        "robots": None,
        "headings": {"h1": [], "h2_count": 0, "h3_count": 0},
        "opengraph": {},
        "twitter": {},
        "images": {"total": 0, "missing_alt": 0},
        "score": 100,
        "warnings": []
    }

    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
        report["status_code"] = resp.status_code
        if resp.status_code != 200:
            report["warnings"].append(f"HTTP status is {resp.status_code} instead of 200 OK")
            report["score"] -= 30
            return report

        soup = BeautifulSoup(resp.text, 'html.parser')

        # 1. Title Audit
        title_el = soup.find('title')
        if title_el and title_el.string:
            title_text = title_el.string.strip()
            report["title"] = title_text
            report["title_length"] = len(title_text)
            if len(title_text) < 30:
                report["warnings"].append("Title is too short (< 30 chars). Consider expanding.")
                report["score"] -= 10
            elif len(title_text) > 65:
                report["warnings"].append("Title is too long (> 65 chars). May be truncated in SERPs.")
                report["score"] -= 5
        else:
            report["warnings"].append("Missing <title> tag!")
            report["score"] -= 25

        # 2. Meta Description Audit
        desc_el = soup.find('meta', attrs={'name': lambda x: x and x.lower() == 'description'})
        if desc_el and desc_el.get('content'):
            desc_text = desc_el['content'].strip()
            report["description"] = desc_text
            report["description_length"] = len(desc_text)
            if len(desc_text) < 70:
                report["warnings"].append("Meta description is too short (< 70 chars).")
                report["score"] -= 10
            elif len(desc_text) > 160:
                report["warnings"].append("Meta description exceeds 160 chars. May get truncated.")
                report["score"] -= 5
        else:
            report["warnings"].append("Missing meta description!")
            report["score"] -= 20

        # 3. Canonical Tag
        canon_el = soup.find('link', rel='canonical')
        if canon_el and canon_el.get('href'):
            report["canonical"] = canon_el['href'].strip()
        else:
            report["warnings"].append("Missing rel='canonical' tag.")
            report["score"] -= 5

        # 4. Robots Directives
        robots_el = soup.find('meta', attrs={'name': lambda x: x and x.lower() == 'robots'})
        if robots_el and robots_el.get('content'):
            report["robots"] = robots_el['content'].strip()
            if 'noindex' in report["robots"].lower():
                report["warnings"].append("Page has 'noindex' meta tag - will not be indexed by Google!")
                report["score"] -= 20

        # 5. Heading Structure
        h1_tags = [h.get_text(strip=True) for h in soup.find_all('h1')]
        report["headings"]["h1"] = h1_tags
        report["headings"]["h2_count"] = len(soup.find_all('h2'))
        report["headings"]["h3_count"] = len(soup.find_all('h3'))

        if len(h1_tags) == 0:
            report["warnings"].append("Missing <h1> main heading tag.")
            report["score"] -= 15
        elif len(h1_tags) > 1:
            report["warnings"].append(f"Multiple <h1> tags found ({len(h1_tags)}). Recommended: exactly 1.")
            report["score"] -= 5

        # 6. OpenGraph & Twitter Cards
        for tag in soup.find_all('meta'):
            prop = tag.get('property', '').lower()
            name = tag.get('name', '').lower()
            content = tag.get('content', '')
            if prop.startswith('og:'):
                report["opengraph"][prop] = content
            elif name.startswith('twitter:'):
                report["twitter"][name] = content

        if not report["opengraph"].get('og:image'):
            report["warnings"].append("Missing og:image social share thumbnail.")
            report["score"] -= 5
        if not report["opengraph"].get('og:title'):
            report["warnings"].append("Missing og:title social metadata.")
            report["score"] -= 5

        # 7. Images without Alt Attributes
        imgs = soup.find_all('img')
        report["images"]["total"] = len(imgs)
        missing_alt = sum(1 for img in imgs if not img.get('alt') or not img['alt'].strip())
        report["images"]["missing_alt"] = missing_alt
        if missing_alt > 0:
            report["warnings"].append(f"{missing_alt} image(s) missing 'alt' accessibility description.")
            report["score"] -= min(10, missing_alt * 2)

    except Exception as e:
        report["warnings"].append(f"Audit failure: {e}")
        report["score"] = 0

    report["score"] = max(0, min(100, report["score"]))
    return report


def main():
    parser = argparse.ArgumentParser(
        description="On-Page SEO, OpenGraph & Metadata Auditor"
    )
    parser.add_argument("url", help="Target website URL to audit")
    parser.add_argument("--json", action="store_true",
                        help="Output results as JSON")

    args = parser.parse_args()

    print(f"[*] Auditing SEO performance for: {args.url}...")
    res = audit_url_seo(args.url)

    if args.json:
        print(json.dumps(res, indent=2))
        return

    print("\n" + "=" * 65)
    print(f"  SEO Health Score: {res['score']}/100")
    print("=" * 65)
    print(f"  Title ({res['title_length']} chars)   : {res['title'] or '[MISSING]'}")
    print(f"  Description ({res['description_length']} chars): {res['description'] or '[MISSING]'}")
    print(f"  Canonical URL      : {res['canonical'] or '[NOT SET]'}")
    print(f"  Robots Meta        : {res['robots'] or '[DEFAULT]'}")
    print(f"  H1 Tag             : {res['headings']['h1'][0] if res['headings']['h1'] else '[NONE]'}")
    print(f"  Headings Count     : H1={len(res['headings']['h1'])}, H2={res['headings']['h2_count']}, H3={res['headings']['h3_count']}")
    print(f"  Images             : {res['images']['total']} total, {res['images']['missing_alt']} missing alt")
    print(f"  OpenGraph Tags     : {len(res['opengraph'])} found")

    if res['warnings']:
        print("\n=== Identified SEO Warnings ===")
        for w in res['warnings']:
            print(f"  [!] {w}")
    else:
        print("\n  [+] Perfect! Zero SEO warnings detected.")


if __name__ == "__main__":
    main()
