#!/usr/bin/env python3
"""
semantic-check-sail.py

Semantic checker for Xebec/SAIL .sail JSON files.

This checker complements JSON Schema validation. JSON Schema validates the file
shape; this script checks reference integrity and practical SAIL modeling rules,
such as diagram references, interface operation ownership, unresolved pathways,
and common decomposition mistakes.

Usage:
  python semantic-check-sail.py path/to/model.sail
  python semantic-check-sail.py path/to/model.sail --json
  python semantic-check-sail.py path/to/model.sail --schema sail-architecture.schema.json
  python semantic-check-sail.py path/to/model.sail --codebook sail-codebook.json

Exit codes:
  0 = no issues at or above the configured fail level
  1 = semantic issues found at or above the configured fail level
  2 = CLI/configuration/file error
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Optional


DEFAULT_OPERATION_TYPES = {
    "One Way",
    "Request / Ack",
    "Request / Response",
    "Streaming",
    "Webhook",
}

# Numeric enum values from current SAIL/Xebec JSON serialization.
ELEMENT_TYPE_NAMES = {
    0: "BoundaryParticipant",
    1: "System",
    2: "Datastore",
    3: "ServiceUnit",
}

INTERACTION_KIND_NAMES = {
    0: "Simple",
    1: "Composite",
    2: "Process",
}

DIAGRAM_TYPE_NAMES = {
    0: "StructuralContext",
    1: "StructuralHierarchical",
    2: "BehavioralContext",
    3: "BehavioralInteraction",
    4: "BehavioralProcess",
    5: "IntrinsicCharacteristicMap",
    6: "Interface",
}

SEVERITY_RANK = {"info": 0, "warning": 1, "error": 2}


@dataclass(order=True)
class Issue:
    sort_key: tuple = field(init=False, repr=False)
    severity: str
    code: str
    path: str
    message: str
    refs: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.sort_key = (-SEVERITY_RANK.get(self.severity, -1), self.code, self.path, self.message)

    def to_json(self) -> dict[str, Any]:
        data = asdict(self)
        data.pop("sort_key", None)
        return data


class Checker:
    def __init__(self, model: dict[str, Any], *, codebook: Optional[dict[str, Any]] = None, strict: bool = False):
        self.model = model
        self.codebook = codebook or {}
        self.strict = strict
        self.issues: list[Issue] = []

        inventory = self._dict(model.get("Inventory"))
        self.structural_elements = self._dict(inventory.get("StructuralElements"))
        self.interactions = self._dict(inventory.get("Interactions"))
        self.communication_pathways = self._dict(inventory.get("CommunicationPathways"))
        self.interfaces = self._dict(inventory.get("Interfaces"))

        self.operation_types = self._load_operation_types()
        self.operations_by_id = self._build_operations_by_id()
        self.diagrams_by_id = self._build_diagrams_by_id()
        self.diagram_container_by_id = self._build_diagram_container_by_id()
        self.placement = self._build_placement_index()

    @staticmethod
    def _dict(value: Any) -> dict[str, Any]:
        return value if isinstance(value, dict) else {}

    @staticmethod
    def _list(value: Any) -> list[Any]:
        return value if isinstance(value, list) else []

    @staticmethod
    def _blank(value: Any) -> bool:
        return value is None or (isinstance(value, str) and not value.strip())

    @staticmethod
    def _name(item: Any, fallback: str) -> str:
        if isinstance(item, dict):
            name = item.get("Name") or item.get("Label") or item.get("Title")
            if isinstance(name, str) and name.strip():
                return name.strip()
        return fallback

    def add(self, severity: str, code: str, path: str, message: str, refs: Optional[list[str]] = None) -> None:
        if self.strict and severity == "warning" and code in {
            "SERVICE_UNIT_HAS_SUBDIAGRAM",
            "BOUNDARY_PARTICIPANT_HAS_SUBDIAGRAM",
            "UNKNOWN_OPERATION_TYPE",
            "UNRESOLVED_CHARMAP_REFERENCE",
            "UNRESOLVED_SUBDIAGRAM_REFERENCE",
        }:
            severity = "error"
        self.issues.append(Issue(severity=severity, code=code, path=path, message=message, refs=refs or []))

    def _load_operation_types(self) -> set[str]:
        observed = (
            self.codebook.get("stringEnums", {})
            .get("OperationType", {})
            .get("observedValues")
        )
        if isinstance(observed, list) and all(isinstance(x, str) for x in observed):
            return {x for x in observed if x.strip()}
        return set(DEFAULT_OPERATION_TYPES)

    def _build_operations_by_id(self) -> dict[str, dict[str, Any]]:
        ops: dict[str, dict[str, Any]] = {}
        for interface_id, interface in self.interfaces.items():
            for op_id, op in self._dict(interface.get("Operations")).items():
                if op_id in ops:
                    self.add(
                        "error",
                        "DUPLICATE_OPERATION_ID",
                        f"$.Inventory.Interfaces['{interface_id}'].Operations['{op_id}']",
                        f"Operation id '{op_id}' is used by more than one interface.",
                        [interface_id, op_id],
                    )
                record = dict(op)
                record["_interfaceId"] = interface_id
                record["_operationId"] = op_id
                ops[op_id] = record
        return ops

    def _build_diagrams_by_id(self) -> dict[str, dict[str, Any]]:
        diagrams: dict[str, dict[str, Any]] = {}
        for _, _, diagram in self._iter_diagrams():
            diagram_id = diagram.get("Id")
            if isinstance(diagram_id, str) and diagram_id.strip():
                if diagram_id in diagrams:
                    self.add(
                        "error",
                        "DUPLICATE_DIAGRAM_ID",
                        f"$..[Id='{diagram_id}']",
                        f"Diagram id '{diagram_id}' appears more than once.",
                        [diagram_id],
                    )
                diagrams[diagram_id] = diagram
        return diagrams

    def _build_diagram_container_by_id(self) -> dict[str, str]:
        out: dict[str, str] = {}
        for container, key, diagram in self._iter_diagrams():
            diagram_id = diagram.get("Id")
            if isinstance(diagram_id, str) and diagram_id.strip():
                out[diagram_id] = f"{container}.{key}" if key else container
        return out

    def _build_placement_index(self) -> dict[str, set[str]]:
        placement: dict[str, set[str]] = defaultdict(set)
        for container, key, diagram in self._iter_diagrams():
            diagram_name = diagram.get("Name") or diagram.get("Id") or f"{container}.{key}"
            for element in self._list(diagram.get("Elements")):
                etype = element.get("$type")
                if etype == "DiagramStructuralElement":
                    ref = element.get("StructuralElementId")
                    if isinstance(ref, str) and ref:
                        placement[f"struct:{ref}"].add(str(diagram_name))
                elif etype == "DiagramInteraction":
                    ref = element.get("InteractionId")
                    if isinstance(ref, str) and ref:
                        placement[f"interaction:{ref}"].add(str(diagram_name))
                elif etype == "DiagramOperation":
                    ref = element.get("OperationId")
                    if isinstance(ref, str) and ref:
                        placement[f"operation:{ref}"].add(str(diagram_name))
            for connector in self._list(diagram.get("Connectors")):
                if connector.get("$type") == "DiagramCommunicationPathway":
                    ref = connector.get("CommunicationPathwayId")
                    if isinstance(ref, str) and ref:
                        placement[f"pathway:{ref}"].add(str(diagram_name))
        return placement

    def _iter_diagrams(self) -> Iterable[tuple[str, str, dict[str, Any]]]:
        singletons = ["StructuralContextDiagram", "BehavioralContextDiagram"]
        for name in singletons:
            diagram = self.model.get(name)
            if isinstance(diagram, dict):
                yield name, "", diagram

        dicts = [
            "HierarchicalDiagrams",
            "InteractionDiagrams",
            "CharacteristicMapDiagrams",
            "InterfaceDiagrams",
        ]
        for name in dicts:
            diagrams = self._dict(self.model.get(name))
            for key, diagram in diagrams.items():
                if isinstance(diagram, dict):
                    yield name, key, diagram

    def run(self) -> list[Issue]:
        self.check_top_level()
        self.check_inventory_ids()
        self.check_structural_elements()
        self.check_interactions()
        self.check_interfaces()
        self.check_communication_pathways()
        self.check_diagrams()
        self.check_orphans()
        return sorted(self.issues)

    def check_top_level(self) -> None:
        required = [
            "Inventory",
            "StructuralContextDiagram",
            "HierarchicalDiagrams",
            "BehavioralContextDiagram",
            "InteractionDiagrams",
            "CharacteristicMapDiagrams",
            "InterfaceDiagrams",
            "Notebook",
        ]
        for key in required:
            if key not in self.model:
                self.add("error", "MISSING_TOP_LEVEL_SECTION", f"$.{key}", f"Missing top-level section '{key}'.")

    def check_inventory_ids(self) -> None:
        buckets = [
            ("StructuralElements", self.structural_elements),
            ("Interactions", self.interactions),
            ("CommunicationPathways", self.communication_pathways),
            ("Interfaces", self.interfaces),
        ]
        all_ids: dict[str, str] = {}
        for bucket_name, items in buckets:
            for key, item in items.items():
                if not isinstance(item, dict):
                    self.add("error", "INVALID_INVENTORY_ITEM", f"$.Inventory.{bucket_name}['{key}']", "Inventory item is not an object.")
                    continue
                item_id = item.get("Id")
                if self._blank(item_id):
                    self.add("error", "MISSING_INVENTORY_ID", f"$.Inventory.{bucket_name}['{key}'].Id", "Inventory item has no Id.")
                elif item_id != key:
                    self.add(
                        "warning",
                        "INVENTORY_KEY_ID_MISMATCH",
                        f"$.Inventory.{bucket_name}['{key}'].Id",
                        f"Dictionary key '{key}' does not match item Id '{item_id}'.",
                        [str(key), str(item_id)],
                    )
                if isinstance(item_id, str) and item_id.strip():
                    if item_id in all_ids:
                        self.add(
                            "error",
                            "DUPLICATE_INVENTORY_ID",
                            f"$.Inventory.{bucket_name}['{key}'].Id",
                            f"Inventory id '{item_id}' also appears in {all_ids[item_id]}.",
                            [item_id],
                        )
                    all_ids[item_id] = f"Inventory.{bucket_name}"

    def check_structural_elements(self) -> None:
        for element_id, element in self.structural_elements.items():
            path = f"$.Inventory.StructuralElements['{element_id}']"
            name = self._name(element, element_id)
            element_type = element.get("ElementType")
            subtype = element.get("SubType")

            if element_type not in ELEMENT_TYPE_NAMES:
                self.add("error", "UNKNOWN_STRUCTURAL_ELEMENT_TYPE", f"{path}.ElementType", f"Unknown ElementType '{element_type}' on '{name}'.")

            if self._blank(element.get("Name")):
                self.add("warning", "BLANK_ELEMENT_NAME", f"{path}.Name", f"Structural element '{element_id}' has a blank name.", [element_id])

            if element_type in {0, 1, 2, 3} and self._blank(subtype):
                self.add("info", "BLANK_ELEMENT_SUBTYPE", f"{path}.SubType", f"Structural element '{name}' has no subtype/kind.", [element_id])

            subdiagram_id = element.get("SubDiagramId")
            if not self._blank(subdiagram_id):
                if subdiagram_id not in self.diagrams_by_id:
                    self.add(
                        "warning",
                        "UNRESOLVED_SUBDIAGRAM_REFERENCE",
                        f"{path}.SubDiagramId",
                        f"'{name}' references missing subdiagram '{subdiagram_id}'.",
                        [element_id, str(subdiagram_id)],
                    )
                if element_type == 0:
                    self.add(
                        "warning",
                        "BOUNDARY_PARTICIPANT_HAS_SUBDIAGRAM",
                        f"{path}.SubDiagramId",
                        f"Boundary participant '{name}' has a subdiagram. Boundary participants are usually external and not decomposed.",
                        [element_id, str(subdiagram_id)],
                    )
                if element_type == 3:
                    self.add(
                        "warning",
                        "SERVICE_UNIT_HAS_SUBDIAGRAM",
                        f"{path}.SubDiagramId",
                        f"Service unit '{name}' has a subdiagram. Service units are usually leaf-level units of responsibility.",
                        [element_id, str(subdiagram_id)],
                    )

            charmap_id = element.get("CharMapDiagramId")
            if not self._blank(charmap_id) and charmap_id not in self._dict(self.model.get("CharacteristicMapDiagrams")):
                self.add(
                    "warning",
                    "UNRESOLVED_CHARMAP_REFERENCE",
                    f"{path}.CharMapDiagramId",
                    f"'{name}' references missing characteristic map diagram '{charmap_id}'.",
                    [element_id, str(charmap_id)],
                )

            represented_ids = self._list(element.get("RepresentedElementIds"))
            for idx, ref_id in enumerate(represented_ids):
                if ref_id not in self.structural_elements:
                    self.add(
                        "error",
                        "UNRESOLVED_REPRESENTED_ELEMENT",
                        f"{path}.RepresentedElementIds[{idx}]",
                        f"'{name}' represents missing structural element '{ref_id}'.",
                        [element_id, str(ref_id)],
                    )
                elif ref_id == element_id:
                    self.add(
                        "warning",
                        "SELF_REPRESENTED_ELEMENT",
                        f"{path}.RepresentedElementIds[{idx}]",
                        f"'{name}' represents itself.",
                        [element_id],
                    )

            if element.get("IsStandIn") is True and not represented_ids:
                self.add(
                    "info",
                    "STANDIN_WITHOUT_REPRESENTED_ELEMENTS",
                    f"{path}.RepresentedElementIds",
                    f"Stand-in element '{name}' does not list represented elements. This may be intentional for a conceptual stand-in.",
                    [element_id],
                )

            cmap = element.get("CharacteristicMap")
            if cmap is not None and not isinstance(cmap, dict):
                self.add("error", "INVALID_CHARACTERISTIC_MAP", f"{path}.CharacteristicMap", f"CharacteristicMap on '{name}' is not an object or null.", [element_id])

    def check_interactions(self) -> None:
        interaction_diagrams = self._dict(self.model.get("InteractionDiagrams"))
        charmap_diagrams = self._dict(self.model.get("CharacteristicMapDiagrams"))
        for interaction_id, interaction in self.interactions.items():
            path = f"$.Inventory.Interactions['{interaction_id}']"
            label = self._name(interaction, interaction_id)
            kind = interaction.get("Kind")
            if kind not in INTERACTION_KIND_NAMES:
                self.add("error", "UNKNOWN_INTERACTION_KIND", f"{path}.Kind", f"Unknown Interaction.Kind '{kind}' on '{label}'.", [interaction_id])
            if self._blank(interaction.get("Label")):
                self.add("warning", "BLANK_INTERACTION_LABEL", f"{path}.Label", f"Interaction '{interaction_id}' has a blank label.", [interaction_id])

            subdiagram_id = interaction.get("SubDiagramId")
            if not self._blank(subdiagram_id) and subdiagram_id not in interaction_diagrams:
                self.add(
                    "warning",
                    "UNRESOLVED_INTERACTION_SUBDIAGRAM",
                    f"{path}.SubDiagramId",
                    f"Interaction '{label}' references missing interaction subdiagram '{subdiagram_id}'.",
                    [interaction_id, str(subdiagram_id)],
                )

            charmap_id = interaction.get("CharMapDiagramId")
            if not self._blank(charmap_id) and charmap_id not in charmap_diagrams:
                self.add(
                    "warning",
                    "UNRESOLVED_INTERACTION_CHARMAP",
                    f"{path}.CharMapDiagramId",
                    f"Interaction '{label}' references missing characteristic map diagram '{charmap_id}'.",
                    [interaction_id, str(charmap_id)],
                )

    def check_interfaces(self) -> None:
        interface_diagrams = self._dict(self.model.get("InterfaceDiagrams"))
        seen_operation_ids: set[str] = set()
        for interface_id, interface in self.interfaces.items():
            path = f"$.Inventory.Interfaces['{interface_id}']"
            name = self._name(interface, interface_id)
            if self._blank(interface.get("Name")):
                self.add("warning", "BLANK_INTERFACE_NAME", f"{path}.Name", f"Interface '{interface_id}' has a blank name.", [interface_id])
            if self._blank(interface.get("Description")):
                self.add("info", "BLANK_INTERFACE_DESCRIPTION", f"{path}.Description", f"Interface '{name}' has no description.", [interface_id])

            diagram_id = interface.get("InterfaceDiagramId")
            if not self._blank(diagram_id) and diagram_id not in interface_diagrams:
                self.add(
                    "warning",
                    "UNRESOLVED_INTERFACE_DIAGRAM",
                    f"{path}.InterfaceDiagramId",
                    f"Interface '{name}' references missing interface diagram '{diagram_id}'.",
                    [interface_id, str(diagram_id)],
                )

            ops = self._dict(interface.get("Operations"))
            if not ops:
                self.add("warning", "INTERFACE_WITHOUT_OPERATIONS", f"{path}.Operations", f"Interface '{name}' has no operations.", [interface_id])

            for op_id, op in ops.items():
                op_path = f"{path}.Operations['{op_id}']"
                op_name = self._name(op, op_id)
                if op_id in seen_operation_ids:
                    self.add("error", "DUPLICATE_OPERATION_ID", op_path, f"Operation id '{op_id}' is duplicated.", [op_id])
                seen_operation_ids.add(op_id)

                if self._blank(op.get("Name")):
                    self.add("warning", "BLANK_OPERATION_NAME", f"{op_path}.Name", f"Operation '{op_id}' has a blank name.", [interface_id, op_id])
                if self._blank(op.get("Description")):
                    self.add("info", "BLANK_OPERATION_DESCRIPTION", f"{op_path}.Description", f"Operation '{op_name}' has no description.", [interface_id, op_id])

                owner_id = op.get("OwnerId")
                if not self._blank(owner_id) and owner_id != interface_id:
                    self.add(
                        "warning",
                        "OPERATION_OWNER_MISMATCH",
                        f"{op_path}.OwnerId",
                        f"Operation '{op_name}' OwnerId '{owner_id}' does not match parent interface id '{interface_id}'.",
                        [interface_id, op_id, str(owner_id)],
                    )

                operation_type = op.get("OperationType")
                if self._blank(operation_type):
                    self.add("warning", "BLANK_OPERATION_TYPE", f"{op_path}.OperationType", f"Operation '{op_name}' has no operation type.", [interface_id, op_id])
                elif operation_type not in self.operation_types:
                    self.add(
                        "warning",
                        "UNKNOWN_OPERATION_TYPE",
                        f"{op_path}.OperationType",
                        f"Operation '{op_name}' uses unknown OperationType '{operation_type}'. Expected one of: {', '.join(sorted(self.operation_types))}.",
                        [interface_id, op_id, str(operation_type)],
                    )

    def check_communication_pathways(self) -> None:
        for pathway_id, pathway in self.communication_pathways.items():
            path = f"$.Inventory.CommunicationPathways['{pathway_id}']"
            source_id = pathway.get("SourceId")
            target_id = pathway.get("TargetId")
            interface_id = pathway.get("InterfaceId")
            operation_id = pathway.get("InterfaceOperationId")

            source = self.structural_elements.get(source_id)
            target = self.structural_elements.get(target_id)

            if self._blank(source_id):
                self.add("error", "BLANK_PATHWAY_SOURCE", f"{path}.SourceId", f"Communication pathway '{pathway_id}' has no SourceId.", [pathway_id])
            elif source is None:
                self.add("error", "UNRESOLVED_PATHWAY_SOURCE", f"{path}.SourceId", f"Communication pathway '{pathway_id}' references missing source '{source_id}'.", [pathway_id, str(source_id)])

            if self._blank(target_id):
                self.add("error", "BLANK_PATHWAY_TARGET", f"{path}.TargetId", f"Communication pathway '{pathway_id}' has no TargetId.", [pathway_id])
            elif target is None:
                self.add("error", "UNRESOLVED_PATHWAY_TARGET", f"{path}.TargetId", f"Communication pathway '{pathway_id}' references missing target '{target_id}'.", [pathway_id, str(target_id)])

            if not self._blank(source_id) and source_id == target_id:
                self.add("warning", "SELF_REFERENTIAL_PATHWAY", path, f"Communication pathway '{pathway_id}' connects an element to itself.", [pathway_id, str(source_id)])

            if self._blank(interface_id) and self._blank(operation_id):
                self.add(
                    "info",
                    "PATHWAY_WITHOUT_INTERFACE",
                    path,
                    f"Communication pathway '{pathway_id}' has no interface or operation assigned.",
                    [pathway_id],
                )
            elif self._blank(interface_id) and not self._blank(operation_id):
                self.add(
                    "error",
                    "PATHWAY_OPERATION_WITHOUT_INTERFACE",
                    f"{path}.InterfaceOperationId",
                    f"Communication pathway '{pathway_id}' references operation '{operation_id}' but no interface.",
                    [pathway_id, str(operation_id)],
                )
            elif not self._blank(interface_id) and interface_id not in self.interfaces:
                self.add(
                    "error",
                    "UNRESOLVED_PATHWAY_INTERFACE",
                    f"{path}.InterfaceId",
                    f"Communication pathway '{pathway_id}' references missing interface '{interface_id}'.",
                    [pathway_id, str(interface_id)],
                )

            if not self._blank(operation_id):
                operation = self.operations_by_id.get(operation_id)
                if operation is None:
                    self.add(
                        "error",
                        "UNRESOLVED_PATHWAY_OPERATION",
                        f"{path}.InterfaceOperationId",
                        f"Communication pathway '{pathway_id}' references missing interface operation '{operation_id}'.",
                        [pathway_id, str(operation_id)],
                    )
                elif not self._blank(interface_id) and operation.get("_interfaceId") != interface_id:
                    self.add(
                        "error",
                        "PATHWAY_OPERATION_INTERFACE_MISMATCH",
                        f"{path}.InterfaceOperationId",
                        f"Pathway operation '{operation_id}' belongs to interface '{operation.get('_interfaceId')}', not pathway interface '{interface_id}'.",
                        [pathway_id, str(interface_id), str(operation_id)],
                    )

            if source is not None and target is not None:
                source_type = source.get("ElementType")
                target_type = target.get("ElementType")
                source_name = self._name(source, str(source_id))
                target_name = self._name(target, str(target_id))
                if source_type == 0 and target_type == 0:
                    self.add(
                        "warning",
                        "BOUNDARY_TO_BOUNDARY_PATHWAY",
                        path,
                        f"Communication pathway connects boundary participant '{source_name}' directly to boundary participant '{target_name}'. Usually communication crosses the system boundary through a system.",
                        [pathway_id, str(source_id), str(target_id)],
                    )

    def check_diagrams(self) -> None:
        expected_container_types = {
            "StructuralContextDiagram": {0},
            "BehavioralContextDiagram": {2},
            "HierarchicalDiagrams": {1},
            "CharacteristicMapDiagrams": {5},
            "InterfaceDiagrams": {6},
        }

        for container, key, diagram in self._iter_diagrams():
            path = f"$.{container}" if not key else f"$.{container}['{key}']"
            diagram_id = diagram.get("Id")
            diagram_name = self._name(diagram, str(diagram_id or key or container))
            diagram_type = diagram.get("Type")
            expected_types = expected_container_types.get(container)
            if expected_types and diagram_type not in expected_types:
                expected_names = ", ".join(DIAGRAM_TYPE_NAMES.get(t, str(t)) for t in sorted(expected_types))
                actual_name = DIAGRAM_TYPE_NAMES.get(diagram_type, str(diagram_type))
                self.add(
                    "warning",
                    "DIAGRAM_TYPE_CONTAINER_MISMATCH",
                    f"{path}.Type",
                    f"Diagram '{diagram_name}' is in {container} but has Type '{actual_name}'. Expected: {expected_names}.",
                    [str(diagram_id)],
                )

            if container == "InteractionDiagrams" and diagram_type not in {3, 4}:
                actual_name = DIAGRAM_TYPE_NAMES.get(diagram_type, str(diagram_type))
                self.add(
                    "warning",
                    "INTERACTION_DIAGRAM_TYPE_MISMATCH",
                    f"{path}.Type",
                    f"Interaction diagram '{diagram_name}' has Type '{actual_name}'. Expected BehavioralInteraction or BehavioralProcess.",
                    [str(diagram_id)],
                )

            if container == "CharacteristicMapDiagrams":
                element_id = diagram.get("ElementId")
                if self._blank(element_id):
                    self.add("error", "CHARMAP_WITHOUT_ELEMENT", f"{path}.ElementId", f"Characteristic map diagram '{diagram_name}' has no ElementId.", [str(diagram_id)])
                elif element_id not in self.structural_elements and element_id not in self.interactions:
                    self.add(
                        "error",
                        "UNRESOLVED_CHARMAP_ELEMENT",
                        f"{path}.ElementId",
                        f"Characteristic map diagram '{diagram_name}' references missing element/interaction '{element_id}'.",
                        [str(diagram_id), str(element_id)],
                    )

            if container == "InterfaceDiagrams":
                interface_id = diagram.get("InterfaceId")
                if self._blank(interface_id):
                    self.add("error", "INTERFACE_DIAGRAM_WITHOUT_INTERFACE", f"{path}.InterfaceId", f"Interface diagram '{diagram_name}' has no InterfaceId.", [str(diagram_id)])
                elif interface_id not in self.interfaces:
                    self.add(
                        "error",
                        "UNRESOLVED_INTERFACE_DIAGRAM_INTERFACE",
                        f"{path}.InterfaceId",
                        f"Interface diagram '{diagram_name}' references missing interface '{interface_id}'.",
                        [str(diagram_id), str(interface_id)],
                    )

            self.check_diagram_elements(path, diagram)
            self.check_diagram_connectors(path, diagram)

    def check_diagram_elements(self, diagram_path: str, diagram: dict[str, Any]) -> None:
        element_ids: set[str] = set()
        for idx, element in enumerate(self._list(diagram.get("Elements"))):
            element_path = f"{diagram_path}.Elements[{idx}]"
            diagram_element_id = element.get("Id")
            if self._blank(diagram_element_id):
                self.add("error", "DIAGRAM_ELEMENT_WITHOUT_ID", f"{element_path}.Id", "Diagram element has no Id.")
            elif diagram_element_id in element_ids:
                self.add("error", "DUPLICATE_DIAGRAM_ELEMENT_ID", f"{element_path}.Id", f"Diagram element id '{diagram_element_id}' is duplicated within this diagram.", [str(diagram_element_id)])
            else:
                element_ids.add(diagram_element_id)

            etype = element.get("$type")
            if etype == "DiagramStructuralElement":
                ref = element.get("StructuralElementId")
                if self._blank(ref):
                    self.add("error", "DIAGRAM_STRUCTURAL_ELEMENT_WITHOUT_REF", f"{element_path}.StructuralElementId", "DiagramStructuralElement has no StructuralElementId.")
                elif ref not in self.structural_elements:
                    self.add("error", "UNRESOLVED_DIAGRAM_STRUCTURAL_ELEMENT", f"{element_path}.StructuralElementId", f"DiagramStructuralElement references missing structural element '{ref}'.", [str(ref)])

            elif etype == "DiagramInteraction":
                ref = element.get("InteractionId")
                if self._blank(ref):
                    self.add("error", "DIAGRAM_INTERACTION_WITHOUT_REF", f"{element_path}.InteractionId", "DiagramInteraction has no InteractionId.")
                elif ref not in self.interactions:
                    self.add("error", "UNRESOLVED_DIAGRAM_INTERACTION", f"{element_path}.InteractionId", f"DiagramInteraction references missing interaction '{ref}'.", [str(ref)])

            elif etype == "DiagramCharacteristic":
                ref = element.get("StructuralElementId")
                category_id = element.get("CharacteristicCategoryId")
                if self._blank(ref):
                    self.add("error", "DIAGRAM_CHARACTERISTIC_WITHOUT_OWNER", f"{element_path}.StructuralElementId", "DiagramCharacteristic has no StructuralElementId owner reference.")
                elif ref not in self.structural_elements and ref not in self.interactions:
                    self.add("error", "UNRESOLVED_DIAGRAM_CHARACTERISTIC_OWNER", f"{element_path}.StructuralElementId", f"DiagramCharacteristic references missing owner '{ref}'.", [str(ref)])
                elif not self._blank(category_id):
                    owner = self.structural_elements.get(ref) or self.interactions.get(ref) or {}
                    cmap = self._dict(owner.get("CharacteristicMap"))
                    if cmap and category_id not in cmap:
                        self.add(
                            "warning",
                            "UNRESOLVED_CHARACTERISTIC_CATEGORY",
                            f"{element_path}.CharacteristicCategoryId",
                            f"DiagramCharacteristic references category '{category_id}' that is not present on owner '{ref}'.",
                            [str(ref), str(category_id)],
                        )

            elif etype == "DiagramOperation":
                interface_id = element.get("InterfaceId")
                operation_id = element.get("OperationId")
                if self._blank(interface_id):
                    self.add("error", "DIAGRAM_OPERATION_WITHOUT_INTERFACE", f"{element_path}.InterfaceId", "DiagramOperation has no InterfaceId.")
                elif interface_id not in self.interfaces:
                    self.add("error", "UNRESOLVED_DIAGRAM_OPERATION_INTERFACE", f"{element_path}.InterfaceId", f"DiagramOperation references missing interface '{interface_id}'.", [str(interface_id)])
                if self._blank(operation_id):
                    self.add("error", "DIAGRAM_OPERATION_WITHOUT_OPERATION", f"{element_path}.OperationId", "DiagramOperation has no OperationId.")
                elif operation_id not in self.operations_by_id:
                    self.add("error", "UNRESOLVED_DIAGRAM_OPERATION", f"{element_path}.OperationId", f"DiagramOperation references missing operation '{operation_id}'.", [str(operation_id)])
                elif not self._blank(interface_id) and self.operations_by_id[operation_id].get("_interfaceId") != interface_id:
                    self.add(
                        "error",
                        "DIAGRAM_OPERATION_INTERFACE_MISMATCH",
                        f"{element_path}.OperationId",
                        f"DiagramOperation operation '{operation_id}' belongs to interface '{self.operations_by_id[operation_id].get('_interfaceId')}', not diagram operation interface '{interface_id}'.",
                        [str(interface_id), str(operation_id)],
                    )

            elif etype == "DiagramPathwayLabel":
                ref = element.get("CommunicationPathwayId")
                if self._blank(ref):
                    self.add("error", "DIAGRAM_PATHWAY_LABEL_WITHOUT_REF", f"{element_path}.CommunicationPathwayId", "DiagramPathwayLabel has no CommunicationPathwayId.")
                elif ref not in self.communication_pathways:
                    self.add("error", "UNRESOLVED_DIAGRAM_PATHWAY_LABEL", f"{element_path}.CommunicationPathwayId", f"DiagramPathwayLabel references missing communication pathway '{ref}'.", [str(ref)])

            elif etype in {"DiagramContextGroup", "DiagramStart", "DiagramEnd", "DiagramNote", "DiagramProcessStep"}:
                if etype == "DiagramProcessStep":
                    ref = element.get("StructuralElementId")
                    if not self._blank(ref) and ref not in self.structural_elements:
                        self.add("error", "UNRESOLVED_PROCESS_STEP_OWNER", f"{element_path}.StructuralElementId", f"DiagramProcessStep references missing structural element '{ref}'.", [str(ref)])
                    subdiagram_id = element.get("SubDiagramId")
                    if not self._blank(subdiagram_id) and subdiagram_id not in self.diagrams_by_id:
                        self.add("warning", "UNRESOLVED_PROCESS_STEP_SUBDIAGRAM", f"{element_path}.SubDiagramId", f"DiagramProcessStep references missing subdiagram '{subdiagram_id}'.", [str(subdiagram_id)])
            else:
                self.add("warning", "UNKNOWN_DIAGRAM_ELEMENT_TYPE", f"{element_path}.$type", f"Unknown diagram element $type '{etype}'.")

    def check_diagram_connectors(self, diagram_path: str, diagram: dict[str, Any]) -> None:
        diagram_element_ids = {
            element.get("Id")
            for element in self._list(diagram.get("Elements"))
            if isinstance(element, dict) and isinstance(element.get("Id"), str) and element.get("Id").strip()
        }
        connector_ids: set[str] = set()
        for idx, connector in enumerate(self._list(diagram.get("Connectors"))):
            connector_path = f"{diagram_path}.Connectors[{idx}]"
            connector_id = connector.get("Id")
            if self._blank(connector_id):
                self.add("error", "DIAGRAM_CONNECTOR_WITHOUT_ID", f"{connector_path}.Id", "Diagram connector has no Id.")
            elif connector_id in connector_ids:
                self.add("error", "DUPLICATE_DIAGRAM_CONNECTOR_ID", f"{connector_path}.Id", f"Diagram connector id '{connector_id}' is duplicated within this diagram.", [str(connector_id)])
            else:
                connector_ids.add(connector_id)

            source_de_id = connector.get("SourceDiagramElementId")
            target_de_id = connector.get("TargetDiagramElementId")
            if self._blank(source_de_id):
                self.add("error", "CONNECTOR_WITHOUT_SOURCE_DIAGRAM_ELEMENT", f"{connector_path}.SourceDiagramElementId", "Connector has no SourceDiagramElementId.")
            elif source_de_id not in diagram_element_ids:
                self.add("error", "UNRESOLVED_CONNECTOR_SOURCE_DIAGRAM_ELEMENT", f"{connector_path}.SourceDiagramElementId", f"Connector references missing source diagram element '{source_de_id}' in the same diagram.", [str(source_de_id)])

            if self._blank(target_de_id):
                self.add("error", "CONNECTOR_WITHOUT_TARGET_DIAGRAM_ELEMENT", f"{connector_path}.TargetDiagramElementId", "Connector has no TargetDiagramElementId.")
            elif target_de_id not in diagram_element_ids:
                self.add("error", "UNRESOLVED_CONNECTOR_TARGET_DIAGRAM_ELEMENT", f"{connector_path}.TargetDiagramElementId", f"Connector references missing target diagram element '{target_de_id}' in the same diagram.", [str(target_de_id)])

            ctype = connector.get("$type")
            if ctype == "DiagramCommunicationPathway":
                ref = connector.get("CommunicationPathwayId")
                if self._blank(ref):
                    self.add("error", "DIAGRAM_COMM_PATHWAY_WITHOUT_REF", f"{connector_path}.CommunicationPathwayId", "DiagramCommunicationPathway has no CommunicationPathwayId.")
                elif ref not in self.communication_pathways:
                    self.add("error", "UNRESOLVED_DIAGRAM_COMM_PATHWAY", f"{connector_path}.CommunicationPathwayId", f"DiagramCommunicationPathway references missing communication pathway '{ref}'.", [str(ref)])

            elif ctype == "DiagramBehavioralConnector":
                # Xebec exports SourceId/TargetId as plain strings, but observed files may
                # leave them blank and rely on SourceDiagramElementId/TargetDiagramElementId
                # for the rendered connector. Treat blank inventory refs as informational
                # when the rendered diagram endpoints resolve.
                for field_name in ["SourceId", "TargetId"]:
                    ref = connector.get(field_name)
                    if self._blank(ref):
                        self.add("info", f"BEHAVIORAL_CONNECTOR_WITHOUT_{field_name.upper()}", f"{connector_path}.{field_name}", f"Behavioral connector has no {field_name}; using diagram endpoint references only.")
                    elif ref not in self.structural_elements and ref not in self.interactions:
                        self.add("warning", f"UNRESOLVED_BEHAVIORAL_CONNECTOR_{field_name.upper()}", f"{connector_path}.{field_name}", f"Behavioral connector {field_name} '{ref}' does not resolve to a structural element or interaction.", [str(ref)])

            elif ctype == "DiagramConnector":
                # Generic connector has no inventory-level semantic reference.
                pass
            else:
                self.add("warning", "UNKNOWN_DIAGRAM_CONNECTOR_TYPE", f"{connector_path}.$type", f"Unknown diagram connector $type '{ctype}'.")

    def check_orphans(self) -> None:
        # These are intentionally low-severity. Xebec inventories may contain drafts.
        for element_id, element in self.structural_elements.items():
            if not self.placement.get(f"struct:{element_id}"):
                self.add(
                    "info",
                    "UNPLACED_STRUCTURAL_ELEMENT",
                    f"$.Inventory.StructuralElements['{element_id}']",
                    f"Structural element '{self._name(element, element_id)}' is not placed on any diagram.",
                    [element_id],
                )

        for interaction_id, interaction in self.interactions.items():
            if not self.placement.get(f"interaction:{interaction_id}"):
                self.add(
                    "info",
                    "UNPLACED_INTERACTION",
                    f"$.Inventory.Interactions['{interaction_id}']",
                    f"Interaction '{self._name(interaction, interaction_id)}' is not placed on any diagram.",
                    [interaction_id],
                )

        for pathway_id, pathway in self.communication_pathways.items():
            if not self.placement.get(f"pathway:{pathway_id}"):
                source_name = self._name(self.structural_elements.get(pathway.get("SourceId")), str(pathway.get("SourceId")))
                target_name = self._name(self.structural_elements.get(pathway.get("TargetId")), str(pathway.get("TargetId")))
                self.add(
                    "info",
                    "UNPLACED_COMMUNICATION_PATHWAY",
                    f"$.Inventory.CommunicationPathways['{pathway_id}']",
                    f"Communication pathway '{source_name} -> {target_name}' is not placed on any diagram.",
                    [pathway_id],
                )


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


def run_schema_validation(model: dict[str, Any], schema_path: Path, sail_file: Path) -> list[Issue]:
    try:
        from jsonschema import Draft202012Validator
        from jsonschema.exceptions import SchemaError
    except ImportError as e:
        raise ValueError("Missing dependency for --schema: jsonschema. Install with: pip install jsonschema") from e

    schema = load_json_file(schema_path)
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as e:
        return [Issue("error", "SCHEMA_FILE_INVALID", str(schema_path), f"Schema file is invalid: {e.message}")]

    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(model), key=lambda e: list(e.path))
    issues = []
    for e in errors:
        path = json_path(e.path)
        issues.append(Issue("error", "SCHEMA_VALIDATION_ERROR", path, e.message, [str(sail_file), str(schema_path)]))
    return issues


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


def filter_issues(issues: list[Issue], *, include_info: bool, max_issues: int) -> list[Issue]:
    if not include_info:
        issues = [i for i in issues if i.severity != "info"]
    return issues[:max_issues] if max_issues > 0 else issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Run semantic checks against a Xebec/SAIL .sail JSON file.")
    parser.add_argument("sail_file", type=Path, help="Path to the .sail file to check")
    parser.add_argument("--schema", type=Path, help="Optional sail-architecture.schema.json path to run shape validation first")
    parser.add_argument("--codebook", type=Path, help="Optional sail-codebook.json path for observed operation types and enum names")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON output")
    parser.add_argument("--include-info", action="store_true", help="Include informational findings in text/JSON output")
    parser.add_argument("--strict", action="store_true", help="Promote selected SAIL modeling warnings to errors")
    parser.add_argument("--max-issues", type=int, default=200, help="Maximum issues to print. Use 0 for no limit")
    parser.add_argument(
        "--fail-on",
        choices=["error", "warning", "info"],
        default="error",
        help="Minimum severity that causes exit code 1. Defaults to error.",
    )
    args = parser.parse_args()

    try:
        model = load_json_file(args.sail_file)
        if not isinstance(model, dict):
            raise ValueError(f"Expected root JSON object in {args.sail_file}")
        codebook = load_json_file(args.codebook) if args.codebook else None
        if codebook is not None and not isinstance(codebook, dict):
            raise ValueError(f"Expected root JSON object in codebook {args.codebook}")

        schema_issues = run_schema_validation(model, args.schema, args.sail_file) if args.schema else []
        checker = Checker(model, codebook=codebook, strict=args.strict)
        semantic_issues = checker.run()
        issues = sorted(schema_issues + semantic_issues)

    except ValueError as e:
        if args.json:
            print(json.dumps({"valid": False, "kind": "file_or_config_error", "message": str(e)}, indent=2))
        else:
            print(f"Error: {e}", file=sys.stderr)
        return 2

    counts = Counter(issue.severity for issue in issues)
    fail_rank = SEVERITY_RANK[args.fail_on]
    failed = any(SEVERITY_RANK.get(issue.severity, -1) >= fail_rank for issue in issues)
    displayed = filter_issues(issues, include_info=args.include_info, max_issues=args.max_issues)

    result = {
        "semanticValid": not failed,
        "sailFile": str(args.sail_file),
        "schemaFile": str(args.schema) if args.schema else None,
        "codebookFile": str(args.codebook) if args.codebook else None,
        "failOn": args.fail_on,
        "strict": args.strict,
        "issueCounts": {
            "error": counts.get("error", 0),
            "warning": counts.get("warning", 0),
            "info": counts.get("info", 0),
            "total": len(issues),
        },
        "shownIssueCount": len(displayed),
        "issues": [issue.to_json() for issue in displayed],
    }

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        status = "PASS" if not failed else "FAIL"
        print(f"{status}: {args.sail_file}")
        print(
            f"Issues: {counts.get('error', 0)} error(s), "
            f"{counts.get('warning', 0)} warning(s), "
            f"{counts.get('info', 0)} info"
        )
        if not args.include_info and counts.get("info", 0):
            print("Info findings hidden. Re-run with --include-info to show them.")
        if len(displayed) < len([i for i in issues if args.include_info or i.severity != 'info']):
            print(f"Showing first {len(displayed)} issue(s). Re-run with --max-issues 0 to show all.")

        for idx, issue in enumerate(displayed, start=1):
            print(f"\n{idx}. [{issue.severity.upper()}] {issue.code}")
            print(f"   Path: {issue.path}")
            print(f"   {issue.message}")
            if issue.refs:
                print(f"   Refs: {', '.join(issue.refs)}")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
