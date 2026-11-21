#!/usr/bin/env python3
"""
High-Speed Batch Image Compressor & WebP Converter
==================================================
Batch optimizes media for web performance and storage savings:
- Converts bulky PNG/JPG/TIFF assets to modern high-efficiency WebP or compressed JPEG
- Intelligent bicubic downscaling preserving aspect ratio
- Parallel multi-threaded image processing
- Formatted compression yield and savings summary

Keywords: image compressor, webp converter, batch image optimizer, web performance, media pipeline
"""

import os
import sys
import argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Tuple, Optional, Any

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

SUPPORTED_EXTS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}


def format_bytes(size_bytes: int) -> str:
    """Format bytes into readable units."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if abs(size_bytes) < 1024.0:
            return f"{size_bytes:3.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def process_single_image(
    src_path: Path,
    dest_path: Path,
    out_format: str = "webp",
    quality: int = 80,
    max_dimension: Optional[int] = None
) -> Optional[Dict[str, Any]]:
    """Compress and convert an image file."""
    if not HAS_PIL:
        return None

    try:
        orig_size = src_path.stat().st_size
        with Image.open(src_path) as img:
            # Handle RGBA to RGB conversion for JPEG
            if out_format.lower() in ("jpg", "jpeg") and img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            # Resize if max_dimension specified
            if max_dimension:
                width, height = img.size
                if max(width, height) > max_dimension:
                    if width > height:
                        new_w = max_dimension
                        new_h = int(height * (max_dimension / width))
                    else:
                        new_h = max_dimension
                        new_w = int(width * (max_dimension / height))
                    img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

            dest_path.parent.mkdir(parents=True, exist_ok=True)
            fmt_save = "WEBP" if out_format.lower() == "webp" else "JPEG"
            img.save(dest_path, format=fmt_save, quality=quality, optimize=True)

        new_size = dest_path.stat().st_size
        savings_pct = round(((orig_size - new_size) / orig_size) * 100, 1) if orig_size > 0 else 0.0

        return {
            "source": str(src_path),
            "destination": str(dest_path),
            "orig_size": orig_size,
            "new_size": new_size,
            "orig_human": format_bytes(orig_size),
            "new_human": format_bytes(new_size),
            "savings_pct": savings_pct
        }
    except Exception as e:
        return {"source": str(src_path), "error": str(e)}


def optimize_directory(
    input_dir: str,
    output_dir: str,
    out_format: str = "webp",
    quality: int = 80,
    max_dimension: Optional[int] = None,
    threads: int = 4
) -> List[Dict[str, Any]]:
    """Recursively batch optimize images."""
    src_root = Path(input_dir).resolve()
    dest_root = Path(output_dir).resolve()

    tasks = []
    for dirpath, _, filenames in os.walk(src_root):
        for fname in filenames:
            fp = Path(dirpath) / fname
            if fp.suffix.lower() in SUPPORTED_EXTS:
                rel = fp.relative_to(src_root)
                dest_file = dest_root / rel.with_suffix(f".{out_format.lower()}")
                tasks.append((fp, dest_file))

    results = []
    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = {
            executor.submit(process_single_image, s, d, out_format, quality, max_dimension): s
            for s, d in tasks
        }
        for future in as_completed(futures):
            res = future.result()
            if res:
                results.append(res)

    return results


def main():
    parser = argparse.ArgumentParser(
        description="High-Speed Batch Image Compressor & WebP Converter"
    )
    parser.add_argument("input", help="Source folder containing images or single image file")
    parser.add_argument("--output", "-o", required=True,
                        help="Destination directory to save optimized images")
    parser.add_argument("--format", "-f", choices=["webp", "jpeg"], default="webp",
                        help="Target output format (default: webp)")
    parser.add_argument("--quality", "-q", type=int, default=80,
                        help="Compression quality 1-100 (default: 80)")
    parser.add_argument("--max-dim", "-m", type=int, default=None,
                        help="Constrain max width/height dimension in pixels")
    parser.add_argument("--threads", "-t", type=int, default=4,
                        help="Processing threads (default: 4)")

    args = parser.parse_args()

    if not HAS_PIL:
        print("[!] Error: 'pillow' library is required. Install via `pip install pillow`.", file=sys.stderr)
        sys.exit(1)

    inp = Path(args.input)
    if inp.is_file():
        dest = Path(args.output)
        if dest.is_dir() or not dest.suffix:
            dest = dest / f"{inp.stem}.{args.format}"
        res = process_single_image(inp, dest, out_format=args.format, quality=args.quality, max_dimension=args.max_dim)
        if res and "error" not in res:
            print(f"[+] Optimized: {res['orig_human']} -> {res['new_human']} ({res['savings_pct']}% saved) -> {res['destination']}")
        else:
            print(f"[!] Optimization failed: {res.get('error') if res else 'Unknown'}", file=sys.stderr)
        return

    print(f"[*] Scanning '{args.input}' for images to optimize (Target: {args.format.upper()}, Quality: {args.quality})...")
    results = optimize_directory(
        args.input,
        args.output,
        out_format=args.format,
        quality=args.quality,
        max_dimension=args.max_dim,
        threads=args.threads
    )

    valid_runs = [r for r in results if "error" not in r]
    total_orig = sum(r["orig_size"] for r in valid_runs)
    total_new = sum(r["new_size"] for r in valid_runs)
    total_saved = total_orig - total_new
    saved_pct = round((total_saved / total_orig) * 100, 1) if total_orig > 0 else 0.0

    print("\n" + "=" * 70)
    print("Batch Image Optimization Summary")
    print("=" * 70)
    print(f"  Processed Files : {len(valid_runs)}")
    print(f"  Original Volume : {format_bytes(total_orig)}")
    print(f"  Optimized Volume: {format_bytes(total_new)}")
    print(f"  Net Savings     : {format_bytes(total_saved)} ({saved_pct}% reduction)")
    print(f"  Output Directory: {args.output}")


if __name__ == "__main__":
    main()
