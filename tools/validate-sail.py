#!/usr/bin/env python3
"""Validate a SAIL .sail JSON file against sail.schema.json.

Usage:
  python tools/validate-sail.py path/to/model.sail schema/sail.schema.json
"""
import json
import sys
from pathlib import Path

try:
    from jsonschema import Draft202012Validator
except ImportError:
    print("Missing dependency: jsonschema. Install with: pip install jsonschema", file=sys.stderr)
    sys.exit(2)

if len(sys.argv) < 3:
    print("Usage: validate-sail.py MODEL.sail sail.schema.json", file=sys.stderr)
    sys.exit(2)

model_path = Path(sys.argv[1])
schema_path = Path(sys.argv[2])
model = json.loads(model_path.read_text(encoding="utf-8"))
schema = json.loads(schema_path.read_text(encoding="utf-8"))

validator = Draft202012Validator(schema)
errors = sorted(validator.iter_errors(model), key=lambda e: list(e.path))

if not errors:
    print(f"OK: {model_path} validates against {schema_path}")
    sys.exit(0)

print(f"FAILED: {model_path} has {len(errors)} validation error(s):")
for err in errors:
    path = "/".join(str(p) for p in err.path) or "<root>"
    print(f"- {path}: {err.message}")
sys.exit(1)
