import os
from typing import Dict, List, Tuple

import ezdxf
import ifcopenshell.api as ifc_api


Point = Tuple[float, float]


def main() -> None:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.join(base_dir, "test_data")
    os.makedirs(out_dir, exist_ok=True)

    dxf_path = os.path.join(out_dir, "villa_riyadh_plot1042.dxf")
    ifc_path = os.path.join(out_dir, "villa_riyadh_plot1042.ifc")
    pdf_path = os.path.join(out_dir, "villa_riyadh_plot1042.pdf")

    spec = _villa_spec()

    _generate_dxf(dxf_path, spec)
    _generate_ifc(ifc_path, spec)
    _generate_minimal_pdf(pdf_path, spec)

    for p in (dxf_path, ifc_path, pdf_path):
        size = os.path.getsize(p) if os.path.exists(p) else 0
        print(f"Wrote {p} ({size} bytes)")


def _villa_spec() -> Dict:
    plot_w = 25.0
    plot_d = 35.0

    building_w = 15.0
    building_d = 20.0
    building_h = 9.0

    front_setback = 2.5
    side_setback = (plot_w - building_w) / 2.0

    x0 = side_setback
    y0 = front_setback

    rooms = [
        {"name": "Living room", "w": 5.0, "d": 4.0, "x": x0 + 0.0, "y": y0 + 0.0},
        {"name": "Majlis", "w": 4.0, "d": 3.5, "x": x0 + 5.2, "y": y0 + 0.0},
        {"name": "Kitchen", "w": 3.0, "d": 2.5, "x": x0 + 9.6, "y": y0 + 0.0},
        {"name": "Bathroom 1", "w": 2.5, "d": 1.8, "x": x0 + 12.8, "y": y0 + 0.0},
        {"name": "Bathroom 2", "w": 2.0, "d": 1.3, "x": x0 + 12.8, "y": y0 + 2.0},
        {"name": "Bedroom 1 (Master)", "w": 4.0, "d": 3.0, "x": x0 + 0.0, "y": y0 + 5.5},
        {"name": "Bedroom 2", "w": 3.0, "d": 2.5, "x": x0 + 4.5, "y": y0 + 5.5},
        {"name": "Bedroom 3", "w": 3.5, "d": 3.0, "x": x0 + 8.2, "y": y0 + 5.5},
        # Deliberate violation: corridor width = 1.0m (< 1.2m)
        {"name": "Corridor", "w": 8.0, "d": 1.0, "x": x0 + 0.0, "y": y0 + 10.5},
    ]

    doors = [
        {"name": "Main Entrance", "type": "EXTERIOR", "width": 1.1, "x": x0 + building_w / 2.0, "y": y0 + 0.0},
        # Deliberate violation: interior doors 0.80m (< 0.9m)
        {"name": "Interior Door 1", "type": "INTERIOR", "width": 0.8, "x": x0 + 4.0, "y": y0 + 5.5},
        {"name": "Interior Door 2", "type": "INTERIOR", "width": 0.8, "x": x0 + 8.0, "y": y0 + 5.5},
        {"name": "Interior Door 3", "type": "INTERIOR", "width": 0.8, "x": x0 + 2.0, "y": y0 + 10.5},
    ]

    return {
        "plot": {"w": plot_w, "d": plot_d},
        "building": {
            "w": building_w,
            "d": building_d,
            "h": building_h,
            "x": x0,
            "y": y0,
        },
        "setbacks": {
            "front": front_setback,
            "rear": plot_d - (y0 + building_d),
            "side_left": side_setback,
            "side_right": side_setback,
        },
        "rooms": rooms,
        "doors": doors,
    }


def _rect(x: float, y: float, w: float, d: float) -> List[Point]:
    return [(x, y), (x + w, y), (x + w, y + d), (x, y + d)]


def _area(poly: List[Point]) -> float:
    a = 0.0
    for i in range(len(poly)):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % len(poly)]
        a += x1 * y2 - x2 * y1
    return abs(a) / 2.0


def _center(poly: List[Point]) -> Point:
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    return (sum(xs) / float(len(xs)), sum(ys) / float(len(ys)))


def _generate_dxf(path: str, spec: Dict) -> None:
    doc = ezdxf.new(setup=True)
    msp = doc.modelspace()

    for layer in [
        "PLOT_BOUNDARY",
        "BUILDING",
        "WALLS",
        "ANNOTATIONS",
        "DIMENSIONS",
        "DOORS",
    ]:
        if layer not in doc.layers:
            doc.layers.new(name=layer)

    # Plot boundary
    plot_w = float(spec["plot"]["w"])
    plot_d = float(spec["plot"]["d"])
    plot_poly = _rect(0.0, 0.0, plot_w, plot_d)
    msp.add_lwpolyline(plot_poly, close=True, dxfattribs={"layer": "PLOT_BOUNDARY"})

    # Building outline
    b = spec["building"]
    b_poly = _rect(float(b["x"]), float(b["y"]), float(b["w"]), float(b["d"]))
    msp.add_lwpolyline(b_poly, close=True, dxfattribs={"layer": "BUILDING"})

    # Rooms as closed polylines on WALLS layer (so we can compute real areas)
    for room in spec["rooms"]:
        poly = _rect(float(room["x"]), float(room["y"]), float(room["w"]), float(room["d"]))
        msp.add_lwpolyline(poly, close=True, dxfattribs={"layer": "WALLS"})
        cx, cy = _center(poly)
        area = _area(poly)
        label = f"{room['name']}\\PArea: {area:.2f} m2"
        msp.add_mtext(
            label,
            dxfattribs={
                "layer": "ANNOTATIONS",
                "insert": (cx, cy),
                "char_height": 0.25,
            },
        )

    # Some interior wall lines (1-line representation)
    msp.add_line((b["x"], b["y"] + 5.0), (b["x"] + b["w"], b["y"] + 5.0), dxfattribs={"layer": "WALLS"})
    msp.add_line((b["x"], b["y"] + 10.0), (b["x"] + b["w"], b["y"] + 10.0), dxfattribs={"layer": "WALLS"})

    # Building height label (parsed by parser_dxf)
    msp.add_mtext(
        f"Building Height: {float(b['h']):.1f}m",
        dxfattribs={
            "layer": "ANNOTATIONS",
            "insert": (1.0, plot_d - 1.0),
            "char_height": 0.3,
        },
    )

    # Dimensions (lightweight text-based, still on DIMENSIONS layer)
    setbacks = spec["setbacks"]
    msp.add_text(
        f"Front setback = {setbacks['front']}m",
        dxfattribs={"layer": "DIMENSIONS", "height": 0.25, "insert": (1.0, 1.0)},
    )
    msp.add_text(
        f"Side setbacks = {setbacks['side_left']}m",
        dxfattribs={"layer": "DIMENSIONS", "height": 0.25, "insert": (1.0, 1.4)},
    )

    # Door block with width/type/name attributes
    if "PCD_DOOR" not in doc.blocks:
        blk = doc.blocks.new(name="PCD_DOOR")
        blk.add_arc(center=(0, 0), radius=0.5, start_angle=0, end_angle=90)
        blk.add_attdef(tag="WIDTH", insert=(0.6, 0.1), height=0.2)
        blk.add_attdef(tag="TYPE", insert=(0.6, -0.1), height=0.2)
        blk.add_attdef(tag="NAME", insert=(0.6, -0.3), height=0.2)

    for door in spec["doors"]:
        ref = msp.add_blockref(
            "PCD_DOOR",
            insert=(float(door["x"]), float(door["y"])),
            dxfattribs={"layer": "DOORS"},
        )
        ref.add_attrib("WIDTH", str(float(door["width"])), insert=(float(door["x"]) + 0.1, float(door["y"]) + 0.1))
        ref.add_attrib("TYPE", str(door["type"]), insert=(float(door["x"]) + 0.1, float(door["y"]) - 0.1))
        ref.add_attrib("NAME", str(door["name"]), insert=(float(door["x"]) + 0.1, float(door["y"]) - 0.3))

    doc.saveas(path)


def _generate_ifc(path: str, spec: Dict) -> None:
    f = ifc_api.run("project.create_file", version="IFC2X3")

    # Required metadata for IFC2X3 in IfcOpenShell API
    person = ifc_api.run(
        "owner.add_person",
        f,
        identification="U1",
        given_name="PCD",
        family_name="Demo",
    )
    org = ifc_api.run("owner.add_organisation", f, name="Plans & Compliance CoPilot")
    ifc_api.run("owner.add_person_and_organisation", f, person=person, organisation=org)
    ifc_api.run(
        "owner.add_application",
        f,
        application_full_name="pcd-real-engine",
        application_identifier="pcd",
        version="0.1",
    )

    project = ifc_api.run("root.create_entity", f, ifc_class="IfcProject", name="Villa Riyadh Plot 1042")
    site = ifc_api.run("root.create_entity", f, ifc_class="IfcSite", name="Plot 1042")
    building = ifc_api.run("root.create_entity", f, ifc_class="IfcBuilding", name="Villa")
    storey = ifc_api.run("root.create_entity", f, ifc_class="IfcBuildingStorey", name="Ground Floor")
    storey.Elevation = 0.0

    ifc_api.run("aggregate.assign_object", f, products=[site], relating_object=project)
    ifc_api.run("aggregate.assign_object", f, products=[building], relating_object=site)
    ifc_api.run("aggregate.assign_object", f, products=[storey], relating_object=building)

    # Site properties
    plot_area = float(spec["plot"]["w"]) * float(spec["plot"]["d"])
    pset_site = ifc_api.run("pset.add_pset", f, product=site, name="Pset_SiteCommon")
    ifc_api.run("pset.edit_pset", f, pset=pset_site, properties={"PlotArea": plot_area})

    setbacks = spec["setbacks"]
    footprint_area = float(spec["building"]["w"]) * float(spec["building"]["d"])
    pset_setbacks = ifc_api.run("pset.add_pset", f, product=site, name="Pset_PCD_Setbacks")
    ifc_api.run(
        "pset.edit_pset",
        f,
        pset=pset_setbacks,
        properties={
            "FrontSetback": float(setbacks["front"]),
            "RearSetback": float(setbacks["rear"]),
            "SideSetbackLeft": float(setbacks["side_left"]),
            "SideSetbackRight": float(setbacks["side_right"]),
            "BuildingFootprintArea": footprint_area,
        },
    )

    # Building properties
    pset_building = ifc_api.run("pset.add_pset", f, product=building, name="Pset_BuildingCommon")
    ifc_api.run("pset.edit_pset", f, pset=pset_building, properties={"Height": float(spec["building"]["h"])})

    # Spaces
    for room in spec["rooms"]:
        space = ifc_api.run("root.create_entity", f, ifc_class="IfcSpace", name=str(room["name"]))
        space.LongName = _space_category(str(room["name"]))
        ifc_api.run("aggregate.assign_object", f, products=[space], relating_object=storey)

        area = float(room["w"]) * float(room["d"])
        qto = ifc_api.run("pset.add_qto", f, product=space, name="Qto_SpaceBaseQuantities")
        ifc_api.run("pset.edit_qto", f, qto=qto, properties={"NetFloorArea": area})

        if str(room["name"]).lower().startswith("corridor"):
            pset_space = ifc_api.run("pset.add_pset", f, product=space, name="Pset_PCD_Space")
            ifc_api.run("pset.edit_pset", f, pset=pset_space, properties={"ClearWidth": float(room["d"])})

    # Exterior walls (elements)
    for i in range(4):
        wall = ifc_api.run("root.create_entity", f, ifc_class="IfcWall", name=f"Exterior Wall {i+1}")
        ifc_api.run("spatial.assign_container", f, products=[wall], relating_structure=storey)

    # Doors
    for door in spec["doors"]:
        d = ifc_api.run("root.create_entity", f, ifc_class="IfcDoor", name=str(door["name"]))
        d.OverallWidth = float(door["width"])
        ifc_api.run("spatial.assign_container", f, products=[d], relating_structure=storey)

    f.write(path)


def _space_category(name: str) -> str:
    n = (name or "").lower()
    if "bedroom" in n:
        return "Bedroom"
    if "living" in n:
        return "Living"
    if "kitchen" in n:
        return "Kitchen"
    if "bath" in n:
        return "Bathroom"
    if "corridor" in n:
        return "Corridor"
    if "majlis" in n:
        return "Majlis"
    return "Other"


def _generate_minimal_pdf(path: str, spec: Dict) -> None:
    # Minimal 1-page PDF with embedded text. Good enough for pdfplumber text extraction.
    lines = [
        "Plans & Compliance CoPilot — Demo PDF",
        "Villa Riyadh Plot 1042",
        f"Plot: {spec['plot']['w']}m × {spec['plot']['d']}m",
        f"Building: {spec['building']['w']}m × {spec['building']['d']}m, Height {spec['building']['h']}m",
        f"Front setback: {spec['setbacks']['front']}m",
    ]
    text = "\\n".join(lines)
    _write_basic_pdf_with_text(path, text)


def _write_basic_pdf_with_text(path: str, text: str) -> None:
    # Based on a simple PDF object/xref layout.
    def esc(s: str) -> str:
        return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    content_lines = []
    y = 740
    for line in text.split("\\n"):
        content_lines.append(f"BT /F1 12 Tf 72 {y} Td ({esc(line)}) Tj ET")
        y -= 16
    stream = "\n".join(content_lines) + "\n"
    stream_bytes = stream.encode("utf-8")

    objs: List[bytes] = []

    objs.append(b"1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj\n")
    objs.append(b"2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1 >>endobj\n")
    objs.append(
        b"3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources<< /Font<< /F1 4 0 R >> >> /Contents 5 0 R >>endobj\n"
    )
    objs.append(b"4 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>endobj\n")
    objs.append((f"5 0 obj<< /Length {len(stream_bytes)} >>stream\n".encode("ascii") + stream_bytes + b"endstream\nendobj\n"))

    header = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"

    offsets = [0]
    out = bytearray()
    out.extend(header)

    for obj in objs:
        offsets.append(len(out))
        out.extend(obj)

    xref_pos = len(out)
    out.extend(f"xref\n0 {len(offsets)}\n".encode("ascii"))
    out.extend(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        out.extend(f"{off:010d} 00000 n \n".encode("ascii"))

    out.extend(
        (
            f"trailer<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n"
        ).encode("ascii")
    )

    with open(path, "wb") as f:
        f.write(bytes(out))


if __name__ == "__main__":
    main()
