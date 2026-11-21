#!/usr/bin/env python3
"""
Image EXIF Privacy Sanitizer & Geotag Redactor
==============================================
Audits and strips GPS geolocation coordinates, device serials, and camera signatures:
- Inspects EXIF, GPS Info, Camera Make/Model, Software, and Timestamps
- Completely purges privacy-leaking metadata from photos
- Batch directory sanitization
- 100% offline security and privacy protection

Keywords: exif sanitizer, remove gps geotag, photo privacy, metadata stripper, osint defense
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Any

try:
    from PIL import Image, ExifTags
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

SUPPORTED_EXTS = {'.jpg', '.jpeg', '.png', '.tiff', '.webp'}


def _convert_to_degrees(value) -> float:
    """Helper to convert the GPS coordinates stored in EXIF to decimal degrees."""
    try:
        d = float(value[0])
        m = float(value[1])
        s = float(value[2])
        return round(d + (m / 60.0) + (s / 3600.0), 6)
    except Exception:
        return 0.0


def audit_image_exif(image_path: str) -> Dict[str, Any]:
    """Inspect image for sensitive metadata and GPS tags."""
    if not HAS_PIL:
        raise ImportError("pillow is required for EXIF processing.")

    p = Path(image_path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {image_path}")

    report = {
        "file": str(p),
        "has_exif": False,
        "gps_coordinates": None,
        "device_info": {},
        "raw_tags": {}
    }

    try:
        with Image.open(p) as img:
            exif = img.getexif()
            if not exif:
                return report

            report["has_exif"] = True
            gps_info = {}

            for tag_id, val in exif.items():
                tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
                if tag_name == "GPSInfo":
                    # Parse GPS sub-tags
                    gps_data = {}
                    for t_sub, v_sub in val.items():
                        sub_name = ExifTags.GPSTAGS.get(t_sub, str(t_sub))
                        gps_data[sub_name] = str(v_sub)
                    gps_info = gps_data
                elif tag_name in ("Make", "Model", "Software", "DateTime", "Artist", "HostComputer"):
                    report["device_info"][tag_name] = str(val).strip()
                else:
                    report["raw_tags"][tag_name] = str(val)[:80]

            if gps_info:
                lat = None
                lon = None
                if "GPSLatitude" in gps_info and "GPSLatitudeRef" in gps_info:
                    # Decimal degrees
                    lat_ref = gps_info["GPSLatitudeRef"]
                    lat_str = gps_info["GPSLatitude"]
                report["gps_coordinates"] = gps_info

    except Exception as e:
        report["error"] = str(e)

    return report


def strip_image_exif(src_path: Path, dest_path: Path) -> bool:
    """Read image and save clean version without EXIF dictionary."""
    if not HAS_PIL:
        raise ImportError("pillow is required.")

    try:
        with Image.open(src_path) as img:
            # Create fresh copy without metadata
            data = list(img.getdata())
            image_without_exif = Image.new(img.mode, img.size)
            image_without_exif.putdata(data)

            dest_path.parent.mkdir(parents=True, exist_ok=True)
            # Save without exif
            image_without_exif.save(dest_path)
        return True
    except Exception:
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Image EXIF Privacy Sanitizer & Geotag Redactor"
    )
    parser.add_argument("action", choices=["audit", "strip"],
                        help="Action: 'audit' (view metadata) or 'strip' (purge metadata)")
    parser.add_argument("input", help="Image file or directory")
    parser.add_argument("--output", "-o", default=None,
                        help="Destination file or folder (required for strip)")
    parser.add_argument("--json", action="store_true",
                        help="Print audit output in JSON")

    args = parser.parse_args()

    if not HAS_PIL:
        print("[!] Error: 'pillow' is required.", file=sys.stderr)
        sys.exit(1)

    inp = Path(args.input)

    if args.action == "audit":
        if inp.is_file():
            info = audit_image_exif(str(inp))
            if args.json:
                print(json.dumps(info, indent=2))
                return

            print(f"\n=== EXIF Privacy Audit: {inp.name} ===")
            print(f"  EXIF Detected     : {info['has_exif']}")
            if info["device_info"]:
                print("  Device Footprints :")
                for k, v in info["device_info"].items():
                    print(f"    - {k:<15}: {v}")
            if info["gps_coordinates"]:
                print(f"  [!] Geolocation GPS Coordinates Found: {info['gps_coordinates']}")
            if not info["has_exif"]:
                print("  [+] Clean! No metadata found.")
        else:
            print("[!] Directory audit: pass individual image file or use strip action.")

    elif args.action == "strip":
        if not args.output:
            print("[!] Error: '--output' argument is required for strip action.", file=sys.stderr)
            sys.exit(1)

        dest = Path(args.output)
        if inp.is_file():
            ok = strip_image_exif(inp, dest)
            if ok:
                print(f"[+] Successfully purged EXIF metadata -> {dest}")
            else:
                print("[!] Error stripping metadata.", file=sys.stderr)
                sys.exit(1)
        else:
            # Batch directory
            count = 0
            for root, _, files in os.walk(inp):
                for f in files:
                    fp = Path(root) / f
                    if fp.suffix.lower() in SUPPORTED_EXTS:
                        rel = fp.relative_to(inp)
                        target = dest / rel
                        if strip_image_exif(fp, target):
                            count += 1
            print(f"[+] Batch sanitized {count} images into -> {dest}")


if __name__ == "__main__":
    main()
