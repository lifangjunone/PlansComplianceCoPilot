from typing import Any, Dict, List, Optional, Tuple


RULES = [
    {
        "id": "ADG-R-2.3",
        "category": "Setback",
        "desc_en": "Front setback ≥ 3.0m",
        "desc_ar": "الارتداد الأمامي ≥ 3.0 م",
        "field": "front_setback",
        "operator": ">=",
        "threshold": 3.0,
        "unit": "m",
    },
    {
        "id": "ADG-R-2.4",
        "category": "Setback",
        "desc_en": "Side setback ≥ 2.0m",
        "field": "side_setback_min",
        "operator": ">=",
        "threshold": 2.0,
        "unit": "m",
    },
    {
        "id": "ADG-R-2.5",
        "category": "Setback",
        "desc_en": "Rear setback ≥ 3.0m",
        "field": "rear_setback",
        "operator": ">=",
        "threshold": 3.0,
        "unit": "m",
    },
    {
        "id": "SBC-201-4.1",
        "category": "Room Size",
        "desc_en": "Bedroom area ≥ 9.0 m²",
        "field": "bedroom_areas",
        "operator": "each_>=",
        "threshold": 9.0,
        "unit": "m²",
    },
    {
        "id": "SBC-201-4.2",
        "category": "Room Size",
        "desc_en": "Living room area ≥ 12.0 m²",
        "field": "living_area",
        "operator": ">=",
        "threshold": 12.0,
        "unit": "m²",
    },
    {
        "id": "SBC-201-4.3",
        "category": "Room Size",
        "desc_en": "Kitchen area ≥ 5.0 m²",
        "field": "kitchen_area",
        "operator": ">=",
        "threshold": 5.0,
        "unit": "m²",
    },
    {
        "id": "SBC-201-4.4",
        "category": "Room Size",
        "desc_en": "Bathroom area ≥ 3.0 m²",
        "field": "bathroom_areas",
        "operator": "each_>=",
        "threshold": 3.0,
        "unit": "m²",
    },
    {
        "id": "SBC-201-5.1",
        "category": "Circulation",
        "desc_en": "Corridor width ≥ 1.2m",
        "field": "corridor_width",
        "operator": ">=",
        "threshold": 1.2,
        "unit": "m",
    },
    {
        "id": "SBC-201-5.2",
        "category": "Openings",
        "desc_en": "Interior door width ≥ 0.9m",
        "field": "interior_door_widths",
        "operator": "each_>=",
        "threshold": 0.9,
        "unit": "m",
    },
    {
        "id": "SBC-201-5.3",
        "category": "Openings",
        "desc_en": "Exterior door width ≥ 1.0m",
        "field": "exterior_door_width",
        "operator": ">=",
        "threshold": 1.0,
        "unit": "m",
    },
    {
        "id": "ADG-R-3.1",
        "category": "Building",
        "desc_en": "Building height ≤ 12.0m",
        "field": "building_height",
        "operator": "<=",
        "threshold": 12.0,
        "unit": "m",
    },
    {
        "id": "ADG-R-3.2",
        "category": "Building",
        "desc_en": "Lot coverage ≤ 60%",
        "field": "lot_coverage_pct",
        "operator": "<=",
        "threshold": 60.0,
        "unit": "%",
    },
]


def _fmt(value: Any, unit: str) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, (int, float)):
        if unit == "%":
            return f"{float(value):.1f}{unit}"
        if unit == "m":
            return f"{float(value):.2f}{unit}"
        if unit == "m²":
            return f"{float(value):.2f} {unit}"
        return f"{value}{unit}"
    return str(value)


def _get_derived(data: Dict[str, Any], field: str) -> Any:
    derived = data.get("derived") or {}
    if field in derived:
        return derived.get(field)
    # allow direct fields at root for convenience
    return data.get(field)


def check_compliance(parsed: Dict[str, Any]) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    for rule in RULES:
        results.append(_check_rule(parsed, rule))
    return results


def _check_rule(parsed: Dict[str, Any], rule: Dict[str, Any]) -> Dict[str, Any]:
    field = rule.get("field")
    op = rule.get("operator")
    threshold = float(rule.get("threshold"))
    unit = rule.get("unit") or ""

    actual = _get_derived(parsed, field)

    if actual is None:
        return {
            "rule_id": rule.get("id"),
            "category": rule.get("category"),
            "description": rule.get("desc_en"),
            "status": "WARNING",
            "required": f"{op} {threshold}{unit}",
            "actual": "N/A",
            "element": "N/A",
            "reasoning": f"Field '{field}' was not found in parsed data.",
            "corrective_action": "Provide a file that includes this measurement (IFC properties or DXF geometry).",
        }

    if op in (">=", "<="):
        actual_value = float(actual)
        passed = actual_value >= threshold if op == ">=" else actual_value <= threshold
        status = "PASS" if passed else "FAIL"
        deficiency = threshold - actual_value if op == ">=" else actual_value - threshold
        deficiency = max(deficiency, 0.0)

        element, reasoning, action = _default_reasoning(parsed, rule, actual_value, deficiency)

        return {
            "rule_id": rule.get("id"),
            "category": rule.get("category"),
            "description": rule.get("desc_en"),
            "status": status,
            "required": f"{op} {threshold}{unit}",
            "actual": _fmt(actual_value, unit),
            "element": element,
            "reasoning": reasoning,
            "corrective_action": action,
        }

    if op == "each_>=" and isinstance(actual, list):
        failing: List[Dict[str, Any]] = []
        for item in actual:
            v = float(item.get("value")) if isinstance(item, dict) else float(item)
            name = item.get("name") if isinstance(item, dict) else None
            if v < threshold:
                failing.append({"name": name or "(unknown)", "value": v})

        passed = len(failing) == 0
        status = "PASS" if passed else "FAIL"

        if passed:
            element = "All elements"
            reasoning = f"All values meet the requirement of ≥ {threshold}{unit}."
            action = "No action required."
            actual_str = ", ".join([_fmt(float(item.get("value")), unit) for item in actual if isinstance(item, dict)])
            actual_str = actual_str or "All ≥ threshold"
        else:
            element = ", ".join([f["name"] for f in failing])
            min_def = min([threshold - f["value"] for f in failing])
            reasoning = (
                f"The following elements are below the minimum of {threshold}{unit}: "
                + "; ".join([f"{f['name']}={_fmt(f['value'], unit)}" for f in failing])
                + f". Minimum deficiency = {min_def:.2f}{unit}."
            )
            action = "Increase the affected room/door size(s) to meet the minimum requirement."
            actual_str = "; ".join([f"{f['name']}: {_fmt(f['value'], unit)}" for f in failing])

        return {
            "rule_id": rule.get("id"),
            "category": rule.get("category"),
            "description": rule.get("desc_en"),
            "status": status,
            "required": f"≥ {threshold}{unit}",
            "actual": actual_str,
            "element": element,
            "reasoning": reasoning,
            "corrective_action": action,
        }

    return {
        "rule_id": rule.get("id"),
        "category": rule.get("category"),
        "description": rule.get("desc_en"),
        "status": "WARNING",
        "required": f"{op} {threshold}{unit}",
        "actual": str(actual),
        "element": "N/A",
        "reasoning": f"Unsupported operator '{op}' or unexpected data type for field '{field}'.",
        "corrective_action": "Update the rule engine implementation.",
    }


def _default_reasoning(
    parsed: Dict[str, Any],
    rule: Dict[str, Any],
    actual_value: float,
    deficiency: float,
) -> Tuple[str, str, str]:
    rule_id = rule.get("id")
    threshold = float(rule.get("threshold"))
    unit = rule.get("unit") or ""

    if rule_id == "ADG-R-2.3":
        return (
            "Front boundary to building face (south)",
            f"Measured distance from plot south boundary to nearest building wall = {_fmt(actual_value, unit)}. "
            f"Rule {rule_id} requires minimum {threshold}{unit}. Deficiency = {deficiency:.2f}{unit}.",
            "Move building north by at least the deficiency, or reduce building depth.",
        )

    if rule_id in ("ADG-R-2.4", "ADG-R-2.5"):
        return (
            "Plot boundary to building face",
            f"Computed setback = {_fmt(actual_value, unit)} vs required {threshold}{unit}.",
            "Adjust building position to satisfy required setbacks.",
        )

    if rule_id == "SBC-201-4.2":
        return (
            "Living room",
            f"Living room area = {_fmt(actual_value, unit)} vs required ≥ {threshold}{unit}.",
            "Increase living room area by adjusting internal layout.",
        )

    if rule_id == "SBC-201-4.3":
        return (
            "Kitchen",
            f"Kitchen area = {_fmt(actual_value, unit)} vs required ≥ {threshold}{unit}.",
            "Increase kitchen area by adjusting internal layout.",
        )

    if rule_id == "SBC-201-5.1":
        return (
            "Corridor",
            f"Corridor width = {_fmt(actual_value, unit)} vs required ≥ {threshold}{unit}. Deficiency = {deficiency:.2f}{unit}.",
            "Widen corridor clear width by relocating adjacent walls.",
        )

    if rule_id == "SBC-201-5.3":
        return (
            "Main entrance",
            f"Exterior door width = {_fmt(actual_value, unit)} vs required ≥ {threshold}{unit}.",
            "Increase the exterior door leaf/opening width.",
        )

    if rule_id == "ADG-R-3.1":
        excess = deficiency
        return (
            "Building",
            f"Building height = {_fmt(actual_value, unit)} vs maximum {threshold}{unit}. Excess = {excess:.2f}{unit}.",
            "Reduce building height (fewer storeys or lower floor-to-floor height).",
        )

    if rule_id == "ADG-R-3.2":
        excess = deficiency
        return (
            "Plot coverage",
            f"Lot coverage = {_fmt(actual_value, unit)} vs maximum {threshold}{unit}. Excess = {excess:.1f}{unit}.",
            "Reduce building footprint area or increase plot area.",
        )

    return (
        "N/A",
        f"Actual value = {_fmt(actual_value, unit)}; threshold = {threshold}{unit}.",
        "No action required." if deficiency == 0 else "Adjust design to meet this requirement.",
    )
