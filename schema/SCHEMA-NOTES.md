# Schema Notes

## Confirmed enum mappings supplied

The following enum mappings were supplied and are included in `sail-codebook.json`:

- `InteractionKind`: `0=Simple`, `1=Composite`, `2=Process`
- `StructuralElementType`: `0=BoundaryParticipant`, `1=System`, `2=Datastore`, `3=ServiceUnit`
- `DiagramType`: `0=StructuralContext`, `1=StructuralHierarchical`, `2=BehavioralContext`, `3=BehavioralInteraction`, `4=BehavioralProcess`, `5=IntrinsicCharacteristicMap`, `6=Interface`
- `AssumptionType`
- `DecisionStatus`
- `ReferenceType`
- `RiskImpact`
- `RiskStatus`
- `TodoStatus`
- `TodoPriority`

## Confirmed DiagramElementEdge mapping

`DiagramElementEdge` has been supplied and is included in `sail-codebook.json`:

- `0=None`
- `1=Top`
- `2=Bottom`
- `3=Left`
- `4=Right`

The schema now constrains `SourceEdge` and `TargetEdge` to those values.

## Still worth confirming

The examples contain `OperationType` as strings, including:

- `One Way`
- `Request / Ack`
- `Request / Response`
- `Streaming`
- `Webhook`

If these are formal enums in code, they can be added as a confirmed enum later.

## Notebook item shapes

The supplied examples have empty Notebook arrays, so the schema intentionally leaves notebook entry objects permissive. Once populated examples are available, the schema can be tightened for decisions, todos, assumptions, risks, journal entries, references, and stakeholders.
