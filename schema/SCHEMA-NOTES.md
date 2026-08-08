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

## Automatic connection points

`SourceIsDynamic` and `TargetIsDynamic` (booleans) were added to `DiagramConnectorBase`,
`DiagramBehavioralConnector`, and `DiagramCommunicationPathway`. They mark a connector end as
*automatic*: the editor recalculates that end's edge and offset whenever either attached element is
moved or resized, instead of leaving it where the author placed it.

Two properties of the design matter to anyone reading a `.sail`:

- **`SourceEdge`/`SourceOffset` remain the authoritative values** and are rewritten on every
  recalculation. A consumer that ignores these flags still renders the connector in the right place.
  The flags only say whether the editor is free to move the point.
- **Both are optional — deliberately.** Every other property in these three blocks is listed in
  `required`, and all three set `"additionalProperties": false`. Adding these to `required` would
  invalidate every `.sail` written before the feature existed; omitting them from `properties` would
  invalidate every one written after. They are therefore in `properties` only. Keep it that way, and
  apply the same reasoning to any future connector property.

Note these definitions are flat rather than composed — `DiagramConnector` is a `oneOf` over the three,
each repeating the base properties — so a new connector property has to be added in all three places.

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
