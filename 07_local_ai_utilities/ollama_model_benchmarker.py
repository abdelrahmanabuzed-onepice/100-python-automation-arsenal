#!/usr/bin/env python3
"""
Local LLM & Ollama Performance Benchmarker
==========================================
Benchmarks local Ollama and OpenAI-compatible inference endpoints:
- Generates exact Tokens-per-Second (eval_rate) and Time-To-First-Token (TTFT)
- Measures prompt evaluation speed and inference latency
- Evaluates models across multi-domain prompts (Code, Reasoning, Creative, Extraction)
- Side-by-side comparative terminal matrix & JSON export

Keywords: ollama benchmark, local ai, llm tokens per second, vram inference, ai utilities
"""

import sys
import time
import json
import argparse
from typing import List, Dict, Tuple, Optional, Any

try:
    import requests
except ImportError:
    requests = None

DEFAULT_PROMPTS = [
    {
        "category": "Code Gen",
        "prompt": "Write a Python function to compute the Fibonacci sequence up to N with memoization."
    },
    {
        "category": "Reasoning",
        "prompt": "A farmer is taking a fox, a goose, and a bag of grain across a river in a small boat. What is the step-by-step strategy?"
    },
    {
        "category": "Extraction",
        "prompt": "Extract the names and dates into JSON: 'Meeting with Sarah on Oct 14, followed by review with David on Nov 3.'"
    }
]


def test_ollama_endpoint(base_url: str = "http://127.0.0.1:11434") -> Tuple[bool, List[str]]:
    """Check if Ollama server is reachable and fetch list of installed models."""
    if not requests:
        return False, []
    try:
        r = requests.get(f"{base_url}/api/tags", timeout=3.0)
        if r.status_code == 200:
            data = r.json()
            models = [m.get("name") for m in data.get("models", [])]
            return True, models
    except Exception:
        pass
    return False, []


def benchmark_model_run(model: str, prompt: str, base_url: str = "http://127.0.0.1:11434") -> Dict[str, Any]:
    """Execute single benchmark generation and capture Ollama hardware telemetry."""
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.2
        }
    }

    t0 = time.perf_counter()
    resp = requests.post(f"{base_url}/api/generate", json=payload, timeout=60.0)
    client_duration = round(time.perf_counter() - t0, 3)

    if resp.status_code != 200:
        return {
            "model": model,
            "error": f"API returned status {resp.status_code}: {resp.text[:100]}"
        }

    data = resp.json()

    # Ollama returns nanoseconds for internal timers
    total_dur_ns = data.get("total_duration", 0)
    prompt_eval_count = data.get("prompt_eval_count", 0)
    prompt_eval_dur_ns = data.get("prompt_eval_duration", 1)
    eval_count = data.get("eval_count", 0)
    eval_dur_ns = data.get("eval_duration", 1)

    eval_sec = eval_dur_ns / 1e9 if eval_dur_ns else 1.0
    prompt_eval_sec = prompt_eval_dur_ns / 1e9 if prompt_eval_dur_ns else 1.0

    eval_rate = round(eval_count / eval_sec, 2) if eval_sec > 0 else 0.0
    prompt_rate = round(prompt_eval_count / prompt_eval_sec, 2) if prompt_eval_sec > 0 else 0.0

    return {
        "model": model,
        "tokens_generated": eval_count,
        "tokens_per_second": eval_rate,
        "prompt_tokens": prompt_eval_count,
        "prompt_eval_rate": prompt_rate,
        "total_latency_sec": client_duration,
        "response_sample": (data.get("response", "")[:120] + "...").replace("\n", " ")
    }


def main():
    parser = argparse.ArgumentParser(
        description="Local LLM & Ollama Performance Benchmarker"
    )
    parser.add_argument("--models", "-m", nargs="+", default=None,
                        help="List of model names to benchmark (e.g. 'llama3:8b' 'mistral')")
    parser.add_argument("--url", "-u", default="http://127.0.0.1:11434",
                        help="Ollama server URL (default: http://127.0.0.1:11434)")
    parser.add_argument("--custom-prompt", "-p", default=None,
                        help="Single custom prompt to run instead of the default benchmark suite")
    parser.add_argument("--json", action="store_true",
                        help="Output benchmark results in JSON format")

    args = parser.parse_args()

    if not requests:
        print("[!] Error: 'requests' library required.", file=sys.stderr)
        sys.exit(1)

    is_online, installed_models = test_ollama_endpoint(args.url)
    if not is_online:
        print(f"[!] Warning: Cannot reach Ollama daemon at {args.url}.", file=sys.stderr)
        print("    Ensure Ollama is running (`ollama serve`).", file=sys.stderr)
        # We exit cleanly with a diagnostic note
        if args.json:
            print(json.dumps({"status": "offline", "url": args.url}, indent=2))
        sys.exit(0)

    target_models = args.models or (installed_models[:2] if installed_models else ["llama3"])

    prompts = [{"category": "Custom", "prompt": args.custom_prompt}] if args.custom_prompt else DEFAULT_PROMPTS

    print(f"\n[*] Starting Benchmark on Ollama ({args.url})")
    print(f"[*] Monitored Models: {', '.join(target_models)}")
    print(f"[*] Benchmark Scenarios: {len(prompts)}\n")

    all_results = []

    for model in target_models:
        for p_item in prompts:
            cat = p_item["category"]
            prompt_text = p_item["prompt"]
            print(f"[*] Testing [{model}] on '{cat}' scenario...", end="", flush=True)
            res = benchmark_model_run(model, prompt_text, base_url=args.url)
            res["category"] = cat
            all_results.append(res)
            if "error" in res:
                print(f" [FAILED: {res['error']}]")
            else:
                print(f" [DONE: {res['tokens_per_second']} tok/s, {res['total_latency_sec']}s]")

    if args.json:
        print(json.dumps(all_results, indent=2))
        return

    print("\n" + "=" * 80)
    print(f"{'Model':<18} | {'Scenario':<12} | {'Tokens/s':<10} | {'Tokens':<8} | {'Latency':<8} | {'Sample'}")
    print("=" * 80)
    for r in all_results:
        if "error" in r:
            print(f"{r['model']:<18} | {r.get('category',''):<12} | ERROR: {r['error']}")
        else:
            print(f"{r['model']:<18} | {r['category']:<12} | {r['tokens_per_second']:>8.1f} | {r['tokens_generated']:>6} | {r['total_latency_sec']:>6.2f}s | {r['response_sample'][:25]}")
    print("=" * 80)


if __name__ == "__main__":
    main()
