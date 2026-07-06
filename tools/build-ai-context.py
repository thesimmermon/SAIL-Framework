#!/usr/bin/env python3
"""Build a derived AI-friendly SAIL context summary from a canonical .sail file.

The canonical .sail file is unchanged. This script adds resolved enum names and
common reference names to produce a compact context file for AI coding agents.

Usage:
  python tools/build-ai-context.py GridGuard.sail schema/sail-codebook.json > GridGuard.ai-context.json
"""
import json
import sys
from pathlib import Path

if len(sys.argv) < 3:
    print("Usage: build-ai-context.py MODEL.sail sail-codebook.json", file=sys.stderr)
    sys.exit(2)

model = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
codebook = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))

def enum_name(enum_name, value):
    values = codebook.get("numericEnums", {}).get(enum_name, {}).get("values", {})
    item = values.get(str(value))
    return item.get("name") if isinstance(item, dict) else None

inventory = model.get("Inventory", {})
struct = inventory.get("StructuralElements", {})
interactions = inventory.get("Interactions", {})
interfaces = inventory.get("Interfaces", {})
pathways = inventory.get("CommunicationPathways", {})

ops_by_id = {}
for interface_id, interface in interfaces.items():
    for op_id, op in interface.get("Operations", {}).items():
        ops_by_id[op_id] = {"interfaceId": interface_id, "interfaceName": interface.get("Name"), **op}

summary = {
    "architectureName": model.get("Name"),
    "sourceModel": Path(sys.argv[1]).name,
    "note": "Derived AI context. The .sail file remains canonical.",
    "structuralElements": [],
    "interactions": [],
    "interfaces": [],
    "communicationPathways": []
}

for element_id, element in struct.items():
    summary["structuralElements"].append({
        "id": element_id,
        "name": element.get("Name"),
        "elementType": element.get("ElementType"),
        "elementTypeName": enum_name("StructuralElementType", element.get("ElementType")),
        "subType": element.get("SubType"),
        "description": element.get("Description"),
        "refinement": element.get("Refinement"),
        "isStandIn": element.get("IsStandIn"),
        "subDiagramId": element.get("SubDiagramId"),
        "characteristicMapDiagramId": element.get("CharMapDiagramId")
    })

for interaction_id, interaction in interactions.items():
    summary["interactions"].append({
        "id": interaction_id,
        "label": interaction.get("Label"),
        "kind": interaction.get("Kind"),
        "kindName": enum_name("InteractionKind", interaction.get("Kind")),
        "subDiagramId": interaction.get("SubDiagramId"),
        "characteristicMapDiagramId": interaction.get("CharMapDiagramId")
    })

for interface_id, interface in interfaces.items():
    summary["interfaces"].append({
        "id": interface_id,
        "name": interface.get("Name"),
        "description": interface.get("Description"),
        "version": interface.get("Version"),
        "documentationLocation": interface.get("DocumentationLocation"),
        "interfaceDiagramId": interface.get("InterfaceDiagramId"),
        "operations": [
            {
                "id": op_id,
                "name": op.get("Name"),
                "operationType": op.get("OperationType"),
                "description": op.get("Description"),
                "ownerId": op.get("OwnerId")
            }
            for op_id, op in interface.get("Operations", {}).items()
        ]
    })

for pathway_id, pathway in pathways.items():
    source = struct.get(pathway.get("SourceId"), {})
    target = struct.get(pathway.get("TargetId"), {})
    interface = interfaces.get(pathway.get("InterfaceId"), {})
    operation = ops_by_id.get(pathway.get("InterfaceOperationId"), {})
    summary["communicationPathways"].append({
        "id": pathway_id,
        "sourceId": pathway.get("SourceId"),
        "sourceName": source.get("Name"),
        "sourceTypeName": enum_name("StructuralElementType", source.get("ElementType")) if source else None,
        "targetId": pathway.get("TargetId"),
        "targetName": target.get("Name"),
        "targetTypeName": enum_name("StructuralElementType", target.get("ElementType")) if target else None,
        "interfaceId": pathway.get("InterfaceId"),
        "interfaceName": interface.get("Name"),
        "interfaceOperationId": pathway.get("InterfaceOperationId"),
        "interfaceOperationName": operation.get("Name")
    })

print(json.dumps(summary, indent=2))
