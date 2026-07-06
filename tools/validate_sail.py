#!/usr/bin/env python3
"""
validate_sail.py

Simple CLI validator for Xebec/SAIL .sail files using a JSON Schema.

Usage:
  python validate_sail.py path/to/model.sail
  python validate_sail.py path/to/model.sail --schema path/to/sail-architecture.schema.json
  python validate_sail.py path/to/model.sail --json

Exit codes:
  0 = valid
  1 = invalid JSON or schema validation failed
  2 = CLI/configuration error
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    from jsonschema import Draft202012Validator
    from jsonschema.exceptions import SchemaError
except ImportError:  # pragma: no cover
    print(
        "Missing dependency: jsonschema\n"
        "Install it with: pip install jsonschema",
        file=sys.stderr,
    )
    sys.exit(2)


def load_json_file(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8-sig") as f:
            return json.load(f)
    except FileNotFoundError:
        raise ValueError(f"File not found: {path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {path}: {e.msg} at line {e.lineno}, column {e.colno}")
    except OSError as e:
        raise ValueError(f"Could not read {path}: {e}")


def json_path(error_path: Any) -> str:
    parts = list(error_path)
    if not parts:
        return "$"
    out = "$"
    for part in parts:
        if isinstance(part, int):
            out += f"[{part}]"
        else:
            escaped = str(part).replace("'", "\\'")
            out += f"['{escaped}']"
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a Xebec/SAIL .sail JSON file against a JSON Schema.")
    parser.add_argument("sail_file", type=Path, help="Path to the .sail file to validate")
    parser.add_argument(
        "--schema",
        type=Path,
        default=Path(__file__).with_name("sail-architecture.schema.json"),
        help="Path to the SAIL JSON Schema file. Defaults to sail-architecture.schema.json next to this script.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON output")
    parser.add_argument("--max-errors", type=int, default=50, help="Maximum validation errors to print")
    args = parser.parse_args()

    try:
        schema = load_json_file(args.schema)
        sail_doc = load_json_file(args.sail_file)

        # Validate the schema itself first so schema mistakes are caught early.
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema)
        errors = sorted(validator.iter_errors(sail_doc), key=lambda e: list(e.path))

    except SchemaError as e:
        result = {
            "valid": False,
            "kind": "schema_error",
            "message": str(e),
            "schemaFile": str(args.schema),
        }
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"Schema error in {args.schema}:\n{e}", file=sys.stderr)
        return 2
    except ValueError as e:
        result = {
            "valid": False,
            "kind": "file_error",
            "message": str(e),
        }
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(str(e), file=sys.stderr)
        return 1

    if not errors:
        result = {
            "valid": True,
            "sailFile": str(args.sail_file),
            "schemaFile": str(args.schema),
            "errorCount": 0,
        }
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"VALID: {args.sail_file}")
        return 0

    formatted_errors = []
    for e in errors[: args.max_errors]:
        formatted_errors.append(
            {
                "path": json_path(e.path),
                "message": e.message,
                "validator": e.validator,
                "schemaPath": json_path(e.schema_path),
            }
        )

    result = {
        "valid": False,
        "sailFile": str(args.sail_file),
        "schemaFile": str(args.schema),
        "errorCount": len(errors),
        "shownErrorCount": len(formatted_errors),
        "errors": formatted_errors,
    }

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"INVALID: {args.sail_file}")
        print(f"{len(errors)} schema validation error(s). Showing {len(formatted_errors)}:")
        for idx, err in enumerate(formatted_errors, start=1):
            print(f"\n{idx}. {err['path']}")
            print(f"   {err['message']}")
            print(f"   validator: {err['validator']}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
