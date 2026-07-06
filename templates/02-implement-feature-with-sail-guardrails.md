# Implement Feature Using SAIL Guardrails

Task:

{{TASK_DESCRIPTION}}

Relevant files:

- `{{SAIL_MODEL_FILE}}`
- `sail.schema.json`
- `sail-codebook.json`

Before implementation:

1. Validate the model structure against `sail.schema.json`.
2. Use `sail-codebook.json` to interpret enum values.
3. Identify the affected structural elements, interactions, interfaces, operations, and characteristic maps.
4. Confirm the requested behavior fits an existing interaction/process or explicitly flag the missing architecture definition.
5. Confirm the implementation does not bypass defined interfaces or move responsibilities to the wrong service unit.

Implementation rules:

- Do not treat an external BoundaryParticipant as code you can modify.
- Do not bypass an Interface or Operation that is defined in the model.
- Do not add a dependency not represented by a CommunicationPathway without flagging the model update.
- Preserve any latency, reliability, security, offline, integration, or scaling constraints captured in characteristic maps.

Return:

1. SAIL impact summary
2. Implementation plan
3. Code changes
4. Architecture conflicts, if any
5. Model updates required, if any
