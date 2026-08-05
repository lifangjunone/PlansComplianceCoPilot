import os
import tempfile
from typing import Any, Dict, List, Optional

import aiofiles
import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from pydantic import BaseModel

from parser_dxf import parse_dxf
from parser_ifc import parse_ifc
from parser_pdf import parse_pdf
from rule_engine import RULES, check_compliance


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_DATA_DIR = os.path.join(BASE_DIR, "test_data")
DEFAULT_DXF = "villa_riyadh_plot1042.dxf"
DEFAULT_IFC = "villa_riyadh_plot1042.ifc"


class CheckRequest(BaseModel):
    parsed_data: Dict[str, Any]


app = FastAPI(
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> Dict[str, Any]:
    return {"status": "ok"}


@app.get("/api/rules")
def list_rules() -> Dict[str, Any]:
    return {"rules": RULES}


TEST_DATA_META = {
    ".dxf": {
        "type": "DXF",
        "kind": "2D CAD drawing (AutoCAD Drawing Exchange Format)",
        "description": "Villa floor plan: plot boundary, building outline, room polygons and doors. Parsed by ezdxf to extract setbacks, room areas, corridor and door widths.",
        "parsed_by": "ezdxf",
        "mime": "application/dxf",
    },
    ".ifc": {
        "type": "IFC",
        "kind": "BIM model (Industry Foundation Classes)",
        "description": "Building Information Model of the same villa (spaces, storeys, quantities). Parsed by IfcOpenShell to extract building height and space quantities.",
        "parsed_by": "IfcOpenShell",
        "mime": "application/x-step",
    },
    ".pdf": {
        "type": "PDF",
        "kind": "Submission document (vector PDF)",
        "description": "Planning submission sheet. Text and vector lines are extracted by pdfplumber (used as supporting evidence; IFC/DXF are the geometric source of truth).",
        "parsed_by": "pdfplumber",
        "mime": "application/pdf",
    },
}


def _test_data_entry(name: str) -> Dict[str, Any]:
    full = os.path.join(TEST_DATA_DIR, name)
    ext = os.path.splitext(name)[1].lower()
    meta = TEST_DATA_META.get(ext, {})
    return {
        "name": name,
        "size": os.path.getsize(full),
        "type": meta.get("type", ext.lstrip(".").upper()),
        "kind": meta.get("kind", ""),
        "description": meta.get("description", ""),
        "parsed_by": meta.get("parsed_by", ""),
        "download_url": f"/api/test-data/{name}/download",
        "preview_url": f"/api/test-data/{name}/preview",
    }


@app.get("/api/test-data")
def list_test_data() -> Dict[str, Any]:
    if not os.path.isdir(TEST_DATA_DIR):
        return {"files": []}

    files = []
    for name in sorted(os.listdir(TEST_DATA_DIR)):
        if name.lower().endswith((".dxf", ".ifc", ".pdf")):
            full = os.path.join(TEST_DATA_DIR, name)
            if os.path.isfile(full):
                files.append(_test_data_entry(name))
    return {"files": files}


@app.get("/api/test-data/{name}/download")
def download_test_data(name: str) -> FileResponse:
    safe_name = os.path.basename(name)
    full = os.path.join(TEST_DATA_DIR, safe_name)
    if not os.path.isfile(full):
        raise HTTPException(status_code=404, detail=f"Test file not found: {safe_name}")
    ext = os.path.splitext(safe_name)[1].lower()
    mime = TEST_DATA_META.get(ext, {}).get("mime", "application/octet-stream")
    return FileResponse(full, media_type=mime, filename=safe_name)


@app.get("/api/test-data/{name}/preview")
def preview_test_data(name: str) -> Dict[str, Any]:
    safe_name = os.path.basename(name)
    full = os.path.join(TEST_DATA_DIR, safe_name)
    if not os.path.isfile(full):
        raise HTTPException(status_code=404, detail=f"Test file not found: {safe_name}")

    ext = os.path.splitext(safe_name)[1].lower()
    max_chars = 12000

    if ext in (".dxf", ".ifc"):
        with open(full, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        total_lines = content.count("\n") + 1
        truncated = len(content) > max_chars
        return {
            "name": safe_name,
            "format": "text",
            "language": "dxf" if ext == ".dxf" else "ifc",
            "total_lines": total_lines,
            "truncated": truncated,
            "content": content[:max_chars],
        }

    if ext == ".pdf":
        parsed = parse_pdf(full)
        pages = parsed.get("pages", [])
        text = "\n\n".join(
            f"--- Page {p.get('page_number')} ({p.get('line_count')} vector lines) ---\n{p.get('text', '')}"
            for p in pages
        )
        truncated = len(text) > max_chars
        return {
            "name": safe_name,
            "format": "text",
            "language": "text",
            "total_lines": text.count("\n") + 1,
            "truncated": truncated,
            "content": text[:max_chars] or "(No extractable text; this PDF is vector/graphics only.)",
        }

    raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")


@app.get("/api/architecture")
def architecture() -> Dict[str, Any]:
    """Feature -> open-source project mapping, used by the Docs view so the
    team can show exactly which OSS project powers each capability."""
    return {
        "features": [
            {
                "feature": "IFC / BIM model parsing",
                "capability": "Reads .ifc models; extracts storeys, spaces, quantities and building height.",
                "oss": "IfcOpenShell",
                "repo": "https://github.com/IfcOpenShell/IfcOpenShell",
                "license": "LGPL-3.0",
                "backend_file": "parser_ifc.py",
            },
            {
                "feature": "DXF / 2D CAD parsing",
                "capability": "Reads .dxf drawings; extracts plot boundary, building outline, room polygons, doors, setbacks and widths.",
                "oss": "ezdxf",
                "repo": "https://github.com/mozman/ezdxf",
                "license": "MIT",
                "backend_file": "parser_dxf.py",
            },
            {
                "feature": "PDF submission extraction",
                "capability": "Extracts text and vector line geometry from planning submission PDFs.",
                "oss": "pdfplumber",
                "repo": "https://github.com/jsvine/pdfplumber",
                "license": "MIT",
                "backend_file": "parser_pdf.py",
            },
            {
                "feature": "Compliance rule engine",
                "capability": "Deterministic checks of extracted quantities against ADG / SBC-201 rules with reasoning + corrective actions.",
                "oss": "buildingSMART IDS (concept) + custom engine",
                "repo": "https://github.com/buildingSMART/IDS",
                "license": "MIT (IDS spec)",
                "backend_file": "rule_engine.py",
            },
            {
                "feature": "Floor-plan overlay (SVG)",
                "capability": "Renders parsed geometry to SVG and highlights violating rooms / setbacks in red.",
                "oss": "ezdxf geometry + custom SVG renderer",
                "repo": "https://github.com/mozman/ezdxf",
                "license": "MIT",
                "backend_file": "main.py (_render_svg)",
            },
            {
                "feature": "Backend API service",
                "capability": "REST API: parse, check, run-full demo, geometry, test-data, docs.",
                "oss": "FastAPI + Uvicorn",
                "repo": "https://github.com/fastapi/fastapi",
                "license": "MIT",
                "backend_file": "main.py",
            },
            {
                "feature": "Web frontend",
                "capability": "Interactive review UI: run demo, upload, results table, overlay, docs and test data.",
                "oss": "React + Vite + Radix UI",
                "repo": "https://github.com/facebook/react",
                "license": "MIT",
                "backend_file": "frontend/src/business.tsx",
            },
        ]
    }


@app.post("/api/parse")
async def parse_endpoint(
    file: Optional[UploadFile] = File(default=None),
    test_file: Optional[str] = Form(default=None),
) -> Dict[str, Any]:
    file_path = None

    if file is not None:
        suffix = os.path.splitext(file.filename or "uploaded")[1]
        fd, tmp_path = tempfile.mkstemp(prefix="pcd_upload_", suffix=suffix)
        os.close(fd)
        async with aiofiles.open(tmp_path, "wb") as f:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                await f.write(chunk)
        file_path = tmp_path

    elif test_file:
        safe_name = os.path.basename(test_file)
        file_path = os.path.join(TEST_DATA_DIR, safe_name)
        if not os.path.isfile(file_path):
            raise HTTPException(status_code=404, detail=f"Test file not found: {safe_name}")

    else:
        raise HTTPException(status_code=400, detail="Provide an uploaded file or test_file")

    parsed = _parse_any(file_path)
    return {"parsed": parsed}


@app.post("/api/check")
def check_endpoint(payload: CheckRequest) -> Dict[str, Any]:
    parsed = payload.parsed_data
    results = check_compliance(parsed)
    summary = {
        "total": len(results),
        "fail": len([r for r in results if r.get("status") == "FAIL"]),
        "pass": len([r for r in results if r.get("status") == "PASS"]),
        "warning": len([r for r in results if r.get("status") == "WARNING"]),
    }
    return {"summary": summary, "results": results}


@app.get("/api/demo/run-full")
def demo_run_full() -> Dict[str, Any]:
    dxf_path = os.path.join(TEST_DATA_DIR, DEFAULT_DXF)
    ifc_path = os.path.join(TEST_DATA_DIR, DEFAULT_IFC)

    if not os.path.isfile(dxf_path) or os.path.getsize(dxf_path) == 0:
        raise HTTPException(
            status_code=500,
            detail=f"Missing demo DXF. Run: python {os.path.join(BASE_DIR, 'generate_test_data.py')}",
        )

    dxf_parsed = parse_dxf(dxf_path)

    ifc_parsed = None
    if os.path.isfile(ifc_path) and os.path.getsize(ifc_path) > 0:
        try:
            ifc_parsed = parse_ifc(ifc_path)
        except Exception as e:
            ifc_parsed = {"error": str(e), "source": "IFC"}

    merged = _merge_parsed(dxf_parsed, ifc_parsed)
    results = check_compliance(merged)

    summary = {
        "total": len(results),
        "fail": len([r for r in results if r.get("status") == "FAIL"]),
        "pass": len([r for r in results if r.get("status") == "PASS"]),
        "warning": len([r for r in results if r.get("status") == "WARNING"]),
    }

    return {
        "default_files": {"dxf": DEFAULT_DXF, "ifc": DEFAULT_IFC},
        "parsed": {"dxf": dxf_parsed, "ifc": ifc_parsed, "merged": merged},
        "compliance": {"summary": summary, "results": results},
    }


@app.get("/api/geometry/svg")
def geometry_svg(test_file: Optional[str] = None) -> Response:
    name = os.path.basename(test_file) if test_file else DEFAULT_DXF
    dxf_path = os.path.join(TEST_DATA_DIR, name)
    if not os.path.isfile(dxf_path):
        raise HTTPException(status_code=404, detail=f"DXF not found: {name}")

    data = parse_dxf(dxf_path)
    results = check_compliance(data)

    svg = _render_svg(data, results)
    return Response(content=svg, media_type="image/svg+xml")


def _parse_any(file_path: str) -> Dict[str, Any]:
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".dxf":
        return parse_dxf(file_path)
    if ext == ".ifc":
        return parse_ifc(file_path)
    if ext == ".pdf":
        return parse_pdf(file_path)
    raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")


def _merge_parsed(dxf_parsed: Dict[str, Any], ifc_parsed: Any) -> Dict[str, Any]:
    merged = {
        "source": "MERGED",
        "file_path": dxf_parsed.get("file_path"),
        "plot": dxf_parsed.get("plot"),
        "building": dxf_parsed.get("building"),
        "rooms": dxf_parsed.get("rooms"),
        "doors": dxf_parsed.get("doors"),
        "derived": dict(dxf_parsed.get("derived") or {}),
    }

    if isinstance(ifc_parsed, dict) and ifc_parsed.get("derived"):
        for k, v in (ifc_parsed.get("derived") or {}).items():
            if merged["derived"].get(k) is None and v is not None:
                merged["derived"][k] = v

    # Prefer DXF setbacks/areas, but allow IFC height override if DXF missing.
    if merged["derived"].get("building_height") is None:
        if isinstance(ifc_parsed, dict):
            merged["derived"]["building_height"] = (ifc_parsed.get("derived") or {}).get("building_height")

    return merged


def _render_svg(dxf: Dict[str, Any], results: List[Dict[str, Any]]) -> str:
    plot = dxf.get("plot") or {}
    building = dxf.get("building") or {}
    rooms = dxf.get("rooms") or []

    plot_bbox = plot.get("bbox") or [0, 0, 25, 35]
    minx, miny, maxx, maxy = [float(x) for x in plot_bbox]

    margin = 1.0
    width = (maxx - minx) + 2 * margin
    height = (maxy - miny) + 2 * margin

    def map_pt(x: float, y: float):
        # SVG y-axis is down; CAD y-axis is up.
        sx = (x - minx) + margin
        sy = (maxy - y) + margin
        return sx, sy

    # Determine which rooms violate (based on derived values, not text labels)
    violated_rooms = set()
    for r in rooms:
        name = str(r.get("name") or "")
        cat = str(r.get("category") or "")
        area = r.get("area")
        if cat == "Bedroom" and area is not None and float(area) < 9.0:
            violated_rooms.add(name)
        if cat == "Bathroom" and area is not None and float(area) < 3.0:
            violated_rooms.add(name)
        if cat == "Corridor":
            # corridor width derived from bbox in parser
            derived = dxf.get("derived") or {}
            cw = derived.get("corridor_width")
            if cw is not None and float(cw) < 1.2:
                violated_rooms.add(name)

    # Front setback violation
    derived = dxf.get("derived") or {}
    front_setback = derived.get("front_setback")
    front_setback_fail = front_setback is not None and float(front_setback) < 3.0

    def poly(points):
        pts = []
        for p in points:
            x, y = float(p[0]), float(p[1])
            sx, sy = map_pt(x, y)
            pts.append(f"{sx:.3f},{sy:.3f}")
        return " ".join(pts)

    plot_poly = poly(plot.get("boundary") or [])
    building_poly = poly(building.get("outline") or [])

    # Build SVG
    parts: List[str] = []
    parts.append(
        f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {width:.3f} {height:.3f}' width='100%' height='100%'>"
    )
    parts.append(
        "<style>\n"
        ".room{fill:rgba(2,132,199,0.08);stroke:#0f172a;stroke-width:0.04;}\n"
        ".room.violation{fill:rgba(220,38,38,0.18);stroke:#dc2626;stroke-width:0.06;}\n"
        ".plot{fill:none;stroke:#111827;stroke-width:0.08;}\n"
        ".building{fill:none;stroke:#006B3F;stroke-width:0.10;}\n"
        ".setbackfail{stroke:#dc2626;stroke-width:0.08;stroke-dasharray:0.25 0.18;}\n"
        ".label{font-family:ui-sans-serif,system-ui,-apple-system,'Segoe UI',Roboto,Helvetica,Arial; font-size:0.55px; fill:#0f172a;}\n"
        "</style>"
    )

    # Plot and building
    if plot_poly:
        parts.append(f"<polygon class='plot' points='{plot_poly}' />")
    if building_poly:
        parts.append(f"<polygon class='building' points='{building_poly}' />")

    # Rooms
    for r in rooms:
        pts = r.get("polygon") or []
        if not pts:
            continue
        name = str(r.get("name") or "")
        area = r.get("area")
        cls = "room violation" if name in violated_rooms else "room"
        parts.append(f"<polygon class='{cls}' points='{poly(pts)}'><title>{name} — {area:.2f} m²</title></polygon>")

        c = r.get("center") or None
        if c and len(c) == 2:
            sx, sy = map_pt(float(c[0]), float(c[1]))
            parts.append(f"<text class='label' x='{sx:.3f}' y='{sy:.3f}' text-anchor='middle'>{name}</text>")

    # Front setback highlight (south boundary to building south face)
    if front_setback_fail:
        b_bbox = building.get("bbox") or []
        if len(b_bbox) == 4:
            bminx, bminy, bmaxx, _ = [float(x) for x in b_bbox]
            sx1, sy1 = map_pt(bminx, miny)
            sx2, sy2 = map_pt(bminx, bminy)
            parts.append(f"<line class='setbackfail' x1='{sx1:.3f}' y1='{sy1:.3f}' x2='{sx2:.3f}' y2='{sy2:.3f}' />")
            sx3, sy3 = map_pt(bmaxx, miny)
            sx4, sy4 = map_pt(bmaxx, bminy)
            parts.append(f"<line class='setbackfail' x1='{sx3:.3f}' y1='{sy3:.3f}' x2='{sx4:.3f}' y2='{sy4:.3f}' />")

    parts.append("</svg>")
    return "\n".join(parts)


# ---------------------------DO NOT EDIT CODE BELOW THIS LINE---------------------------------
# This is the entry point for the FastAPI application.
if __name__ == "__main__":
    port = int(os.environ.get("_BYTEFAAS_RUNTIME_PORT", 8000))
    config = uvicorn.Config("main:app", port=port, log_level="info", host=None)
    server = uvicorn.Server(config)
    server.run()
# --------------------------------------------------------------------------------------------
