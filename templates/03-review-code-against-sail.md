# Review Code Against SAIL Model

Review the supplied code changes against the SAIL architecture model.

Check for:

- Boundary violations
- Missing or invented interfaces
- Operation type or contract mismatches
- Incorrect responsibility placement
- Datastore ownership violations
- Communication pathways not represented in the model
- Process step omissions
- Retry, acknowledgment, buffering, throttling, or deduplication behavior changes
- Latency, reliability, security, offline-mode, or legacy-integration regressions

Return:

1. Architecture-compliant changes
2. Possible architecture drift
3. Required SAIL model updates
4. Questions for the architect
