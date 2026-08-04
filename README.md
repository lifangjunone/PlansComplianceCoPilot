# Plans & Compliance CoPilot — Real Engine

> An **AI-assisted building-plan compliance checker** for the Saudi MoMAH / NHC context (ADG & Saudi Building Code).
> This is **not a mockup** — it runs real open-source parsing libraries on real building geometry and evaluates real compliance rules.

**Positioning:** AI is *advisory / decision-support*. It automatically screens the **quantitative** subset of ADG/SBC rules (setbacks, room areas, corridor/door widths, height, lot coverage) and produces an explainable, rule-traced report. A licensed human reviewer always makes the final decision (BRD NFR-10).

---

## ✨ Why this repo exists

Earlier feasibility work concluded that a Saudi "Plans & Compliance CoPilot" is achievable **by integrating mature open-source and commercial tools** rather than building everything from scratch. This repository is the **proof**: a working end-to-end pipeline built on real, verifiable open-source projects.

## 🧰 Tech stack — real open-source libraries (no simulation)

| Capability | Library | GitHub | Role in this project |
|---|---|---|---|
| IFC / BIM parsing | **IfcOpenShell** | https://github.com/IfcOpenShell/IfcOpenShell | Read IFC models; extract `IfcSpace` areas, `IfcDoor` widths, building height, site setback property sets |
| 2D CAD (DXF) parsing | **ezdxf** | https://github.com/mozman/ezdxf | Read DXF drawings; extract plot boundary, building outline, room polygons, doors, and compute areas/setbacks |
| PDF vector parsing | **pdfplumber** | https://github.com/jsvine/pdfplumber | Extract vector lines & annotation text from PDF permit drawings |
| API backend | **FastAPI** | https://github.com/fastapi/fastapi | REST API serving parse / check / geometry endpoints |
| Frontend | **React + Vite** | — | Interactive results UI, floor-plan SVG overlay with violation highlights |

> All geometry parsing is performed by the libraries above. The rule engine computes violations from the **actual parsed values**.

---

## 🏗️ Architecture

```
pcd-real-engine/
├── backend/                     # FastAPI service (Python 3.8 compatible)
│   ├── main.py                  # API endpoints + CORS
│   ├── generate_test_data.py    # Uses IfcOpenShell + ezdxf to CREATE the real IFC & DXF test files
│   ├── parser_ifc.py            # Real IFC parsing (IfcOpenShell)
│   ├── parser_dxf.py            # Real DXF parsing (ezdxf)
│   ├── parser_pdf.py            # Real PDF parsing (pdfplumber)
│   ├── rule_engine.py           # ADG/SBC quantitative rules + checker
│   ├── test_data/               # Generated real IFC + DXF (+ PDF) files
│   └── requirements.txt
└── frontend/                    # React + Vite single-page demo UI
    └── src/                     # Upload → parse → check → report → SVG overlay
```

## 🔌 API endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/api/health` | Health check |
| GET | `/api/test-data` | List available test files |
| GET | `/api/rules` | List all ADG/SBC rules |
| POST | `/api/parse` | Upload/select a file → parse (auto-detect IFC/DXF/PDF) |
| POST | `/api/check` | Run compliance rules against parsed data |
| GET | `/api/demo/run-full` | One-click: parse default villa + check all rules |
| GET | `/api/geometry/svg` | Floor plan as SVG with violation highlights |

---

## 🏠 Test data — a code-generated Saudi-style villa

`generate_test_data.py` **actually runs IfcOpenShell and ezdxf** to produce `villa_riyadh_plot1042.ifc` and `villa_riyadh_plot1042.dxf`.

- **Plot:** 25 m × 35 m (875 m²)
- **Building footprint:** 15 m × 20 m (300 m²), 2 stories, 9.0 m tall
- **Rooms:** Living, Master + 2 bedrooms, Kitchen, 2 bathrooms, corridor, Majlis (guest)
- Several parameters are **deliberately non-compliant** to demonstrate real detection.

## ✅ Compliance rules (ADG / Saudi Building Code — quantitative subset)

| Rule ID | Category | Requirement |
|---|---|---|
| ADG-R-2.3 | Setback | Front setback ≥ 3.0 m |
| ADG-R-2.4 | Setback | Side setback ≥ 2.0 m |
| ADG-R-2.5 | Setback | Rear setback ≥ 3.0 m |
| SBC-201-4.1 | Room size | Bedroom area ≥ 9.0 m² |
| SBC-201-4.2 | Room size | Living room area ≥ 12.0 m² |
| SBC-201-4.3 | Room size | Kitchen area ≥ 5.0 m² |
| SBC-201-4.4 | Room size | Bathroom area ≥ 3.0 m² |
| SBC-201-5.1 | Circulation | Corridor width ≥ 1.2 m |
| SBC-201-5.2 | Openings | Interior door width ≥ 0.9 m |
| SBC-201-5.3 | Openings | Exterior door width ≥ 1.0 m |
| ADG-R-3.1 | Building | Building height ≤ 12.0 m |
| ADG-R-3.2 | Building | Lot coverage ≤ 60% |

### 🔎 Violations detected on the demo villa (12 rules → 7 PASS / 5 FAIL)

| ❌ Rule | Required | Actual | Issue |
|---|---|---|---|
| ADG-R-2.3 | ≥ 3.0 m | 2.50 m | Front setback insufficient |
| SBC-201-4.1 | ≥ 9.0 m² | 7.50 m² | Bedroom 2 too small |
| SBC-201-4.4 | ≥ 3.0 m² | 2.60 m² | Bathroom 2 too small |
| SBC-201-5.1 | ≥ 1.2 m | 1.00 m | Corridor too narrow |
| SBC-201-5.2 | ≥ 0.9 m | 0.80 m | 3 interior doors too narrow |

Each result includes the triggered rule, the design element, deterministic reasoning, and a corrective action.

---

## 🚀 Run locally

### Backend
```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt          # installs ifcopenshell, ezdxf, pdfplumber, fastapi, ...
python generate_test_data.py             # generate the real IFC + DXF test files
uvicorn main:app --reload --port 8000
# try it:
curl http://localhost:8000/api/demo/run-full
```

> **IfcOpenShell note:** `pip install ifcopenshell` provides prebuilt wheels for modern Python. The deployment target used here pins Python 3.8; if your Python version has no matching wheel, install a compatible IfcOpenShell build (conda-forge or the official downloads) — see the IfcOpenShell repo.

### Frontend
```bash
cd frontend
cp .env.example .env                      # set VITE_API_URL to your backend URL
npm install
npm run dev                               # http://localhost:5173
```

---

## 📊 Feasibility & benchmarking (background)

This engine is the practical companion to the feasibility analysis, which benchmarks each capability against real open-source repos and shipping products, and lists the items that must be aligned with the customer (fully-automated approval, permit-ready generative design, qualitative/aesthetic clauses, dirty-CAD ingestion, local rule digitization, KPI baselines). The core conclusion: the industry can support this; delivery should integrate mature tools + human-in-the-loop + phased rollout, with realistic targets.

## ⚖️ Scope & honesty notes

- Auto-checks **quantitative** rules only; qualitative/aesthetic clauses are routed to human reviewers.
- Advanced modules (generative floorplans, MEP auto-routing, masterplan simulation, construction-photo vs BIM) are **phased/roadmap**, best delivered via integration (e.g., Autodesk Forma, Endra, OpenSpace).
- Test data is illustrative, based on representative ADG/SBC provisions.

## 📄 License

Provided for demonstration/evaluation. Third-party libraries retain their respective licenses (IfcOpenShell — LGPL-3.0; ezdxf — MIT; pdfplumber — MIT; FastAPI — MIT).
