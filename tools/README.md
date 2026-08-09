# SAIL Schema Validator

Simple validators for Xebec/SAIL `.sail` files.

This validates the **file shape** against `sail-architecture.schema.json`. It does not replace semantic SAIL assessment. After this passes, the course platform should still run semantic checks such as reference resolution, diagram-specific SAIL rules, scenario alignment, and architectural judgment assessment.

Both validators resolve the schema from `../schema/sail-architecture.schema.json` by default. That
file is the single copy; do not place another one next to these scripts, or a schema edit will leave
the validators checking against a stale duplicate. Pass `--schema` only to check against a schema
somewhere else on purpose.

## Python validator

Install dependency:

```bash
pip install jsonschema
```

Validate a file:

```bash
python validate_sail.py path/to/model.sail
```

Use a custom schema path:

```bash
python validate_sail.py path/to/model.sail --schema path/to/sail-architecture.schema.json
```

Emit JSON output:

```bash
python validate_sail.py path/to/model.sail --json
```

## Node.js validator

Install dependency:

```bash
npm install
```

Validate a file:

```bash
node validate-sail.mjs path/to/model.sail
```

Or:

```bash
npm run validate -- path/to/model.sail
```

Use a custom schema path:

```bash
node validate-sail.mjs path/to/model.sail --schema path/to/sail-architecture.schema.json
```

Emit JSON output:

```bash
node validate-sail.mjs path/to/model.sail --json
```

## Exit codes

- `0`: valid
- `1`: invalid `.sail` file or JSON parse error
- `2`: validator usage/configuration error
