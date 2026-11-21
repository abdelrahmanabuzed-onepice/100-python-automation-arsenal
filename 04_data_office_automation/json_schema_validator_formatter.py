#!/usr/bin/env python3
"""
JSON Lint, Schema Validator & Auto-Repair Engine
================================================
Universal JSON inspection, formatting, repair, and schema validation:
- Auto-fixes common syntax errors (trailing commas, single quotes, unquoted keys, Python literals)
- Beautifies with custom indentation or compresses to ultra-dense minified format
- Validates structural keys, types, and required fields against reference schema
- Detailed syntax error diagnostics with line/column pointers

Keywords: json validator, json formatter, json repair, linting, data automation
"""

import sys
import re
import json
import argparse
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional


def repair_malformed_json_string(raw: str) -> str:
    """Attempt heuristic repairs on common JSON formatting defects."""
    s = raw.strip()

    # 1. Replace single quotes around keys or strings with double quotes
    # Match 'key': or 'string_val'
    s = re.sub(r"'([^']*)'", r'"\1"', s)

    # 2. Replace Python literals True, False, None with JSON equivalents
    s = re.sub(r'\bTrue\b', 'true', s)
    s = re.sub(r'\bFalse\b', 'false', s)
    s = re.sub(r'\bNone\b', 'null', s)

    # 3. Strip trailing commas before closing braces/brackets
    s = re.sub(r',\s*(\}|\])', r'\1', s)

    # 4. Wrap unquoted keys (e.g. { name: "value" } -> { "name": "value" })
    s = re.sub(r'([{\[,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', s)

    return s


def validate_schema(data: Any, schema: Dict[str, Any], path: str = "root") -> List[str]:
    """Validate data structure against a simple schema specification."""
    errors = []
    if isinstance(schema, dict) and isinstance(data, dict):
        required_fields = schema.get("__required__", [])
        for req in required_fields:
            if req not in data:
                errors.append(f"Missing required key: '{path}.{req}'")

        for k, expected_type in schema.items():
            if k == "__required__":
                continue
            if k in data:
                val = data[k]
                if expected_type == "string" and not isinstance(val, str):
                    errors.append(f"Type mismatch at '{path}.{k}': expected string, got {type(val).__name__}")
                elif expected_type == "number" and not isinstance(val, (int, float)):
                    errors.append(f"Type mismatch at '{path}.{k}': expected number, got {type(val).__name__}")
                elif expected_type == "boolean" and not isinstance(val, bool):
                    errors.append(f"Type mismatch at '{path}.{k}': expected boolean, got {type(val).__name__}")
                elif expected_type == "array" and not isinstance(val, list):
                    errors.append(f"Type mismatch at '{path}.{k}': expected array, got {type(val).__name__}")
                elif isinstance(expected_type, dict) and isinstance(val, dict):
                    errors.extend(validate_schema(val, expected_type, path=f"{path}.{k}"))

    return errors


def process_json(
    input_text_or_path: str,
    output_path: Optional[str] = None,
    repair: bool = False,
    minify: bool = False,
    indent: int = 2,
    schema_path: Optional[str] = None
) -> Dict[str, Any]:
    """Parse, lint, repair and validate JSON."""
    p = Path(input_text_or_path)
    if p.exists() and p.is_file():
        with open(p, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        source_desc = str(p)
    else:
        content = input_text_or_path
        source_desc = "<inline_string>"

    parsed = None
    parse_error = None
    was_repaired = False

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as e:
        parse_error = f"Line {e.lineno}, Col {e.colno}: {e.msg}"
        if repair:
            repaired_content = repair_malformed_json_string(content)
            try:
                parsed = json.loads(repaired_content)
                was_repaired = True
                parse_error = None
            except json.JSONDecodeError as e2:
                parse_error = f"Auto-repair failed. Line {e2.lineno}, Col {e2.colno}: {e2.msg}"

    schema_errors = []
    if parsed is not None and schema_path:
        sp = Path(schema_path)
        if sp.exists():
            with open(sp, "r", encoding="utf-8") as f:
                schema_data = json.load(f)
            schema_errors = validate_schema(parsed, schema_data)

    if parsed is not None and output_path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            if minify:
                json.dump(parsed, f, separators=(',', ':'))
            else:
                json.dump(parsed, f, indent=indent, ensure_ascii=False)

    return {
        "source": source_desc,
        "valid": parsed is not None,
        "error": parse_error,
        "repaired": was_repaired,
        "schema_valid": len(schema_errors) == 0,
        "schema_errors": schema_errors,
        "output_file": str(output_path) if output_path else None
    }


def main():
    parser = argparse.ArgumentParser(
        description="JSON Lint, Schema Validator & Auto-Repair Engine"
    )
    parser.add_argument("input", help="File path or raw JSON string")
    parser.add_argument("--output", "-o", default=None,
                        help="Path to save formatted JSON")
    parser.add_argument("--repair", "-r", action="store_true",
                        help="Attempt heuristic auto-repair on broken JSON syntax")
    parser.add_argument("--minify", "-m", action="store_true",
                        help="Minify JSON (strip all whitespace and line breaks)")
    parser.add_argument("--indent", "-i", type=int, default=2,
                        help="Indentation spaces for beautify (default: 2)")
    parser.add_argument("--schema", "-s", default=None,
                        help="Path to simple schema JSON definition to validate against")
    parser.add_argument("--json", action="store_true",
                        help="Output report summary as JSON")

    args = parser.parse_args()

    res = process_json(
        args.input,
        output_path=args.output,
        repair=args.repair,
        minify=args.minify,
        indent=args.indent,
        schema_path=args.schema
    )

    if args.json:
        print(json.dumps(res, indent=2))
        return

    print("\n=== JSON Inspection Report ===")
    print(f"  Target Source  : {res['source']}")
    print(f"  Syntax Valid   : {'[PASS]' if res['valid'] else '[FAIL]'}")
    if res['repaired']:
        print("  Auto-Repair    : [SUCCESS] Fixed syntax defects.")
    if res['error']:
        print(f"  Syntax Error   : {res['error']}")
    if args.schema:
        print(f"  Schema Status  : {'[PASS]' if res['schema_valid'] else '[FAIL]'}")
        for err in res['schema_errors']:
            print(f"    - {err}")

    if res['output_file']:
        print(f"  [+] Saved Output -> {res['output_file']}")


if __name__ == "__main__":
    main()
