# SAIL Architecture Context Instructions

You are working inside a software architecture described by SAIL model files.

Use these files as architecture context:

- `sail.schema.json` — validates the structure of the `.sail` JSON file.
- `sail-codebook.json` — explains numeric enum values and diagram/type codes.
- `*.sail` — the canonical architecture model.

Rules:

1. Do not infer the meaning of numeric enum values. Use `sail-codebook.json`.
2. Treat `Inventory` as the canonical source of architecture elements, interactions, communication pathways, and interfaces.
3. Treat diagrams as views over the inventory, not as independent architecture truth.
4. Resolve IDs before making design or implementation claims.
5. Before changing code, identify the affected SAIL structural elements, interactions, interfaces, operations, and characteristics.
6. If the requested change conflicts with SAIL boundaries, responsibilities, interfaces, or constraints, stop and report the conflict.
7. Do not invent new service responsibilities, interfaces, or operations without identifying the required architecture model change.

Output for any implementation task:

- Affected SAIL elements
- Affected interfaces/operations
- Applicable characteristics or constraints
- Implementation plan
- Architecture conflicts or required model updates
