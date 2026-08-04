from typing import Any, Dict, List, Optional


def _ensure_ifcopenshell():
    """Ensure the `ifcopenshell` module is available.

    The deployment runtime validates against Python 3.8, but official IfcOpenShell
    wheels on PyPI require Python >= 3.9/3.10. To keep this demo deployable, we
    install IfcOpenShell using `install-ifcopenshell-python` when needed.
    """

    try:
        import ifcopenshell  # type: ignore

        return ifcopenshell
    except Exception:
        import importlib
        import os
        import subprocess
        import sys

        # 1) Fast path: bundled IfcOpenShell binaries for Python 3.8.
        #    (Avoids downloading during request handling, which can time out in serverless.)
        try:
            if sys.version_info[:2] == (3, 8):
                vendor_root = os.path.join(os.path.dirname(__file__), "vendor_ifcopenshell_py38")
                if os.path.isdir(os.path.join(vendor_root, "ifcopenshell")):
                    if vendor_root not in sys.path:
                        sys.path.insert(0, vendor_root)
                    importlib.invalidate_caches()
                    import ifcopenshell  # type: ignore

                    return ifcopenshell
        except Exception:
            pass

        # 2) Fallback: download IfcOpenShell binaries at runtime.
        try:
            subprocess.check_call([sys.executable, "-m", "install_ifcopenshell_python"])
        except Exception as e:
            raise RuntimeError(
                "IfcOpenShell is required to parse IFC files, but could not be installed. "
                f"Tried 'python -m install_ifcopenshell_python'. Error: {e}"
            )

        importlib.invalidate_caches()
        try:
            import ifcopenshell  # type: ignore

            return ifcopenshell
        except Exception as e:
            raise RuntimeError(f"IfcOpenShell installation completed, but import still failed: {e}")


def parse_ifc(file_path: str) -> Dict[str, Any]:
    ifcopenshell = _ensure_ifcopenshell()
    ifc = ifcopenshell.open(file_path)

    building = _first(ifc.by_type("IfcBuilding"))
    site = _first(ifc.by_type("IfcSite"))

    spaces = list(ifc.by_type("IfcSpace"))
    doors = list(ifc.by_type("IfcDoor"))

    building_height = _get_building_height(building)
    setbacks = _get_setbacks(site)
    plot_area = _get_plot_area(site)

    room_rows: List[Dict[str, Any]] = []
    for s in spaces:
        name = getattr(s, "Name", None) or "(Unnamed)"
        category = getattr(s, "LongName", None) or _categorize_room(name)
        area = _get_space_area(s)
        width = None
        if str(category).lower() == "corridor":
            width = _get_float_pset(s, "Pset_PCD_Space", "ClearWidth")
        room_rows.append({"name": name, "category": category, "area": area, "width": width})

    door_rows: List[Dict[str, Any]] = []
    for d in doors:
        name = getattr(d, "Name", None) or "Door"
        width = getattr(d, "OverallWidth", None)
        door_rows.append({"name": name, "type": _door_type(name), "width": float(width) if width is not None else None})

    footprint_area = None
    if plot_area is not None:
        # coverage can only be computed if we also have a footprint; IFC demo file stores footprint on the site as a property.
        footprint_area = _get_float_pset(site, "Pset_PCD_Setbacks", "BuildingFootprintArea")

    derived = _derive_fields(plot_area, footprint_area, building_height, setbacks, room_rows, door_rows)

    return {
        "source": "IFC",
        "file_path": file_path,
        "plot": {"area": plot_area},
        "building": {"height": building_height, "setbacks": setbacks, "footprint_area": footprint_area},
        "rooms": room_rows,
        "doors": door_rows,
        "derived": derived,
    }


def _first(items):
    return items[0] if items else None


def _categorize_room(name: str) -> str:
    n = (name or "").lower()
    if "bedroom" in n:
        return "Bedroom"
    if "living" in n:
        return "Living"
    if "kitchen" in n:
        return "Kitchen"
    if "bath" in n:
        return "Bathroom"
    if "corridor" in n or "hall" in n:
        return "Corridor"
    if "majlis" in n:
        return "Majlis"
    return "Other"


def _door_type(name: str) -> str:
    n = (name or "").lower()
    return "EXTERIOR" if "main" in n or "entrance" in n or "exterior" in n else "INTERIOR"


def _get_building_height(building) -> Optional[float]:
    if building is None:
        return None

    # Prefer Pset_BuildingCommon.Height (used by our generator)
    height = _get_float_pset(building, "Pset_BuildingCommon", "Height")
    if height is not None:
        return height

    # Fallbacks
    ref = getattr(building, "ElevationOfRefHeight", None)
    if ref is not None:
        try:
            return float(ref)
        except Exception:
            return None
    return None


def _get_plot_area(site) -> Optional[float]:
    if site is None:
        return None
    area = _get_float_pset(site, "Pset_SiteCommon", "PlotArea")
    if area is not None:
        return area
    return None


def _get_setbacks(site) -> Dict[str, Optional[float]]:
    setbacks: Dict[str, Optional[float]] = {
        "front": None,
        "rear": None,
        "side_left": None,
        "side_right": None,
    }
    if site is None:
        return setbacks

    setbacks["front"] = _get_float_pset(site, "Pset_PCD_Setbacks", "FrontSetback")
    setbacks["rear"] = _get_float_pset(site, "Pset_PCD_Setbacks", "RearSetback")
    setbacks["side_left"] = _get_float_pset(site, "Pset_PCD_Setbacks", "SideSetbackLeft")
    setbacks["side_right"] = _get_float_pset(site, "Pset_PCD_Setbacks", "SideSetbackRight")
    return setbacks


def _get_space_area(space) -> Optional[float]:
    # Preferred: Qto_SpaceBaseQuantities.NetFloorArea
    area = _get_quantity_area(space, quantity_name="NetFloorArea")
    if area is not None:
        return area

    # Alternate: Pset_SpaceCommon.NetFloorArea
    area = _get_float_pset(space, "Pset_SpaceCommon", "NetFloorArea")
    return area


def _get_float_pset(product, pset_name: str, prop_name: str) -> Optional[float]:
    if product is None:
        return None
    try:
        for rel in getattr(product, "IsDefinedBy", []) or []:
            prop_def = getattr(rel, "RelatingPropertyDefinition", None)
            if prop_def is None:
                continue
            if prop_def.is_a("IfcPropertySet") and getattr(prop_def, "Name", None) == pset_name:
                for p in getattr(prop_def, "HasProperties", []) or []:
                    if getattr(p, "Name", None) != prop_name:
                        continue
                    val = getattr(p, "NominalValue", None)
                    if val is None:
                        return None
                    try:
                        return float(val.wrappedValue)  # type: ignore
                    except Exception:
                        try:
                            return float(val)
                        except Exception:
                            return None
    except Exception:
        return None
    return None


def _get_quantity_area(product, quantity_name: str) -> Optional[float]:
    if product is None:
        return None
    try:
        for rel in getattr(product, "IsDefinedBy", []) or []:
            prop_def = getattr(rel, "RelatingPropertyDefinition", None)
            if prop_def is None:
                continue
            if not prop_def.is_a("IfcElementQuantity"):
                continue
            for q in getattr(prop_def, "Quantities", []) or []:
                if getattr(q, "Name", None) != quantity_name:
                    continue
                if not q.is_a("IfcQuantityArea"):
                    continue
                val = getattr(q, "AreaValue", None)
                if val is None:
                    continue
                try:
                    return float(val)
                except Exception:
                    return None
    except Exception:
        return None
    return None


def _derive_fields(
    plot_area: Optional[float],
    footprint_area: Optional[float],
    building_height: Optional[float],
    setbacks: Dict[str, Optional[float]],
    rooms: List[Dict[str, Any]],
    doors: List[Dict[str, Any]],
) -> Dict[str, Any]:
    bedrooms = [r for r in rooms if (r.get("category") == "Bedroom")]
    bathrooms = [r for r in rooms if (r.get("category") == "Bathroom")]

    living = next((r for r in rooms if r.get("category") == "Living"), None)
    kitchen = next((r for r in rooms if r.get("category") == "Kitchen"), None)
    corridor = next((r for r in rooms if r.get("category") == "Corridor"), None)

    interior_doors = [d for d in doors if (d.get("type") or "").upper() != "EXTERIOR"]
    exterior_doors = [d for d in doors if (d.get("type") or "").upper() == "EXTERIOR"]

    side_left = setbacks.get("side_left")
    side_right = setbacks.get("side_right")
    side_min = None
    if side_left is not None and side_right is not None:
        side_min = min(float(side_left), float(side_right))

    lot_coverage = None
    if plot_area and footprint_area:
        lot_coverage = (float(footprint_area) / float(plot_area)) * 100.0

    corridor_width = None
    if corridor and corridor.get("width") is not None:
        corridor_width = float(corridor.get("width"))

    return {
        "front_setback": float(setbacks.get("front")) if setbacks.get("front") is not None else None,
        "rear_setback": float(setbacks.get("rear")) if setbacks.get("rear") is not None else None,
        "side_setback_min": side_min,
        "lot_coverage_pct": lot_coverage,
        "building_height": float(building_height) if building_height is not None else None,
        "living_area": float(living.get("area")) if living and living.get("area") is not None else None,
        "kitchen_area": float(kitchen.get("area")) if kitchen and kitchen.get("area") is not None else None,
        "corridor_width": corridor_width,
        "bedroom_areas": [{"name": r.get("name"), "value": float(r.get("area"))} for r in bedrooms if r.get("area") is not None],
        "bathroom_areas": [{"name": r.get("name"), "value": float(r.get("area"))} for r in bathrooms if r.get("area") is not None],
        "interior_door_widths": [{"name": d.get("name"), "value": float(d.get("width"))} for d in interior_doors if d.get("width") is not None],
        "exterior_door_width": float(exterior_doors[0].get("width")) if exterior_doors and exterior_doors[0].get("width") is not None else None,
    }
