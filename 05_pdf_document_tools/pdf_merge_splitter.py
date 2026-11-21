#!/usr/bin/env python3
"""
High-Speed PDF Merger, Splitter & Page Extractor
================================================
Local document manipulation utility for office workflows and confidentiality:
- Merge multiple PDF files into a single structured document
- Split and slice PDFs by page numbers, intervals, or custom ranges (e.g. '1-3,5,8-10')
- Rotate pages in increments of 90 degrees
- 100% offline and telemetry-free

Keywords: pdf merger, pdf splitter, page extractor, pdf tools, office automation
"""

import sys
import argparse
from pathlib import Path
from typing import List, Optional

try:
    from pypdf import PdfReader, PdfWriter
except ImportError:
    try:
        from PyPDF2 import PdfReader, PdfWriter
    except ImportError:
        PdfReader = None
        PdfWriter = None


def parse_page_range(range_str: str, total_pages: int) -> List[int]:
    """Parse string range like '1-3,5,8-10', '2-end', 'all' into 0-indexed list of page numbers."""
    if range_str.strip().lower() in ("all", "*"):
        return list(range(total_pages))

    pages = []
    parts = range_str.split(",")
    for p in parts:
        p = p.strip().lower()
        if "-" in p:
            start_s, end_s = p.split("-", 1)
            start_s = start_s.strip()
            end_s = end_s.strip()
            start_num = int(start_s) if start_s and start_s.isdigit() else 1
            if end_s in ("", "end", "max"):
                end_num = total_pages
            elif end_s.isdigit():
                end_num = int(end_s)
            else:
                end_num = total_pages
            for i in range(start_num, end_num + 1):
                if 1 <= i <= total_pages:
                    pages.append(i - 1)
        elif p in ("end", "last"):
            if total_pages >= 1:
                pages.append(total_pages - 1)
        elif p.isdigit():
            val = int(p)
            if 1 <= val <= total_pages:
                pages.append(val - 1)
    return sorted(list(dict.fromkeys(pages)))


def merge_pdfs(pdf_paths: List[str], output_path: str) -> int:
    """Merge multiple PDF files in given sequence."""
    if not PdfWriter:
        raise ImportError("pypdf is required for PDF operations.")

    writer = PdfWriter()
    total_added = 0

    for path in pdf_paths:
        p = Path(path)
        if not p.exists():
            print(f"[!] Warning: Skipping missing file '{path}'", file=sys.stderr)
            continue
        reader = PdfReader(str(p))
        for page in reader.pages:
            writer.add_page(page)
            total_added += 1

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "wb") as f:
        writer.write(f)

    return total_added


def split_pdf(input_path: str, output_path: str, pages_spec: str, rotate_deg: int = 0) -> int:
    """Extract page ranges from PDF and optionally rotate."""
    if not PdfWriter:
        raise ImportError("pypdf is required for PDF operations.")

    inp = Path(input_path)
    if not inp.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    reader = PdfReader(str(inp))
    total_in_doc = len(reader.pages)
    selected_indices = parse_page_range(pages_spec, total_in_doc)

    if not selected_indices:
        raise ValueError(f"No valid pages selected by range '{pages_spec}' (Total pages: {total_in_doc})")

    writer = PdfWriter()
    for idx in selected_indices:
        page = reader.pages[idx]
        if rotate_deg in (90, 180, 270):
            page.rotate(rotate_deg)
        writer.add_page(page)

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "wb") as f:
        writer.write(f)

    return len(selected_indices)


def get_pdf_info(input_path: str) -> None:
    """Print structural document details."""
    inp = Path(input_path)
    if not inp.exists():
        print(f"[!] File not found: {input_path}", file=sys.stderr)
        return
    reader = PdfReader(str(inp))
    print(f"\n=== PDF Document Summary: {inp.name} ===")
    print(f"  Total Pages : {len(reader.pages)}")
    print(f"  Encrypted   : {reader.is_encrypted}")
    if reader.pages:
        box = reader.pages[0].mediabox
        print(f"  Dimensions  : {round(float(box.width))} x {round(float(box.height))} pt")


def main():
    parser = argparse.ArgumentParser(
        description="High-Speed PDF Merger, Splitter & Page Extractor"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Merge command
    merge_p = subparsers.add_parser("merge", help="Merge multiple PDFs into one")
    merge_p.add_argument("files", nargs="+", help="PDF files to merge in order")
    merge_p.add_argument("--output", "-o", required=True, help="Destination merged PDF path")

    # Split / Extract command
    split_p = subparsers.add_parser("extract", help="Extract page ranges from PDF")
    split_p.add_argument("input", help="Source PDF file")
    split_p.add_argument("--pages", "-p", required=True,
                         help="Page specification (e.g. '1-3', '1,4,7-9', '2-end')")
    split_p.add_argument("--rotate", "-r", type=int, choices=[0, 90, 180, 270], default=0,
                         help="Rotate extracted pages by degrees (default: 0)")
    split_p.add_argument("--output", "-o", required=True, help="Destination PDF path")

    # Info command
    info_p = subparsers.add_parser("info", help="Inspect PDF page count and properties")
    info_p.add_argument("input", help="Source PDF file")

    args = parser.parse_args()

    if args.command == "info":
        get_pdf_info(args.input)
    elif args.command == "merge":
        try:
            count = merge_pdfs(args.files, args.output)
            print(f"[+] Merged {len(args.files)} files ({count} pages) into -> {args.output}")
        except Exception as e:
            print(f"[!] Merge failed: {e}", file=sys.stderr)
            sys.exit(1)
    elif args.command == "extract":
        try:
            count = split_pdf(args.input, args.output, args.pages, rotate_deg=args.rotate)
            print(f"[+] Extracted {count} pages into -> {args.output}")
        except Exception as e:
            print(f"[!] Extraction failed: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
