from typing import Any, Dict


def parse_pdf(file_path: str) -> Dict[str, Any]:
    try:
        import pdfplumber  # type: ignore
    except Exception as e:
        raise RuntimeError(f"pdfplumber is required to parse PDF files: {e}")
    # This is a simplified parser: it extracts text + basic line geometry.
    # A full vector-to-room reconstruction is a large task; for this demo, IFC/DXF
    # are the core sources of truth.
    pages_out = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages[:3]:
            try:
                text = page.extract_text() or ""
            except Exception:
                text = ""
            try:
                lines = page.lines or []
            except Exception:
                lines = []
            pages_out.append(
                {
                    "page_number": page.page_number,
                    "width": page.width,
                    "height": page.height,
                    "text": text,
                    "line_count": len(lines),
                }
            )

    return {
        "source": "PDF",
        "file_path": file_path,
        "pages": pages_out,
    }
