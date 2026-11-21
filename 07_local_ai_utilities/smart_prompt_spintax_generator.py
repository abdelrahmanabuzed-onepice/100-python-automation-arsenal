#!/usr/bin/env python3
"""
Smart Polymorphic Prompt & Spintax Generator
============================================
High-entropy text permutation engine for AI prompting, cold outreach, and testing:
- Solves nested recursive Spintax blocks: `{ {Hi|Hello} {friend|there} | Greetings }`
- Injects dynamic runtime variables (dates, random IDs, recipient names)
- Calculates total theoretical permutation combinatorics
- Evaluates uniqueness & Jaccard diversity scores across generated variants

Keywords: spintax generator, prompt engineering, polymorphic text, email variation, local ai
"""

import sys
import re
import random
import argparse
from datetime import datetime
from typing import List, Dict, Set, Tuple


def spin_text_once(template: str) -> str:
    """Recursively resolve the innermost Spintax {a|b|c} patterns."""
    pattern = re.compile(r'\{([^{}]+)\}')
    while True:
        match = pattern.search(template)
        if not match:
            break
        options = match.group(1).split('|')
        choice = random.choice(options)
        template = template[:match.start()] + choice + template[match.end():]
    return template


def count_permutations(template: str) -> int:
    """Estimate total unique combinatorial variants in spintax template."""
    pattern = re.compile(r'\{([^{}]+)\}')
    total = 1
    # Simple non-nested estimation
    matches = pattern.findall(template)
    for m in matches:
        choices = m.split('|')
        total *= len(choices)
    return max(1, total)


def calculate_jaccard_diversity(texts: List[str]) -> float:
    """Compute average pairwise Jaccard distance (uniqueness) among texts."""
    if len(texts) < 2:
        return 1.0

    token_sets = [set(t.lower().split()) for t in texts]
    total_sim = 0.0
    pairs = 0

    # Sample up to 100 pairs for efficiency
    sample_indices = list(range(len(texts)))
    if len(sample_indices) > 50:
        sample_indices = random.sample(sample_indices, 50)

    for i in range(len(sample_indices)):
        for j in range(i + 1, len(sample_indices)):
            s1 = token_sets[sample_indices[i]]
            s2 = token_sets[sample_indices[j]]
            union = s1.union(s2)
            if union:
                sim = len(s1.intersection(s2)) / len(union)
                total_sim += sim
                pairs += 1

    avg_sim = total_sim / pairs if pairs > 0 else 0.0
    return round(1.0 - avg_sim, 3)  # Diversity = 1 - similarity


def generate_variants(
    template: str,
    count: int = 5,
    variables: Dict[str, str] = None
) -> Tuple[List[str], float, int]:
    """Generate N unique variants and calculate diversity metrics."""
    vars_map = variables or {}
    
    # Pre-substitute variables
    base_text = template
    for k, v in vars_map.items():
        base_text = base_text.replace(f"{{{k}}}", v).replace(f"${{{k}}}", v)

    total_perms = count_permutations(base_text)
    generated = set()
    max_attempts = count * 20
    attempts = 0

    while len(generated) < count and attempts < max_attempts:
        attempts += 1
        spun = spin_text_once(base_text).strip()
        generated.add(spun)

    results = list(generated)
    diversity = calculate_jaccard_diversity(results)

    return results, diversity, total_perms


def main():
    parser = argparse.ArgumentParser(
        description="Smart Polymorphic Prompt & Spintax Generator"
    )
    parser.add_argument("template", nargs="?", default=None,
                        help="Spintax template string or leave blank to test default")
    parser.add_argument("--count", "-n", type=int, default=5,
                        help="Number of unique variants to generate (default: 5)")
    parser.add_argument("--file", "-f", default=None,
                        help="Read spintax template from text file")
    parser.add_argument("--output", "-o", default=None,
                        help="Save generated variants to output file (one per line)")
    parser.add_argument("--vars", nargs="*", default=[],
                        help="Key=Value variables to substitute (e.g. name=Alex date=Today)")

    args = parser.parse_args()

    raw_template = args.template
    if args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                raw_template = f.read()
        except Exception as e:
            print(f"[!] Error loading template file: {e}", file=sys.stderr)
            sys.exit(1)

    if not raw_template:
        raw_template = "{Hey|Hello|Hi} {friend|partner|colleague}, {we are excited to|we're thrilled to|pleased to} announce {the launch of our new tool|our latest update|our automated suite}!"

    # Parse variables
    var_dict = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "random_id": str(random.randint(10000, 99999))
    }
    for item in args.vars:
        if "=" in item:
            k, v = item.split("=", 1)
            var_dict[k.strip()] = v.strip()

    variants, diversity, total_perms = generate_variants(raw_template, count=args.count, variables=var_dict)

    print("\n=== Polymorphic Spintax Generation Summary ===")
    print(f"  Combinatorial Space : ~{total_perms:,} potential variants")
    print(f"  Requested Variants  : {len(variants)}")
    print(f"  Diversity Score     : {diversity * 100:.1f}% (Jaccard Distance)")
    print("-" * 65)

    for idx, v in enumerate(variants, 1):
        print(f"[{idx:02d}] {v}")

    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as f:
                for v in variants:
                    f.write(v + "\n")
            print(f"\n[+] Saved {len(variants)} variants to -> {args.output}")
        except Exception as e:
            print(f"[!] Output write failed: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
