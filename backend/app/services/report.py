"""Medical report analysis: extract lab values from an uploaded PDF/image,
compare against reference ranges, and produce a plain-language report.

Extraction: text PDFs via pdfplumber; scanned PDFs and images via OCR
(PyMuPDF render + Tesseract). Parsing: alias + numeric regex per marker.
No LLM required.
"""
from __future__ import annotations

import io
import re
from typing import Any

from app.services.lab_reference import MARKERS

try:
    import pdfplumber
except Exception:  # pragma: no cover
    pdfplumber = None
try:
    import pymupdf  # PyMuPDF
except Exception:  # pragma: no cover
    pymupdf = None
try:
    import pytesseract
    from PIL import Image
except Exception:  # pragma: no cover
    pytesseract = None
    Image = None


class ReportError(Exception):
    pass


# --------------------------------------------------------------------------- #
# Extraction
# --------------------------------------------------------------------------- #
def _ocr_image_bytes(data: bytes) -> str:
    if pytesseract is None or Image is None:
        return ""
    try:
        img = Image.open(io.BytesIO(data))
        return pytesseract.image_to_string(img)
    except Exception:
        return ""


def _ocr_pdf(data: bytes) -> str:
    if pymupdf is None or pytesseract is None:
        return ""
    text = []
    try:
        doc = pymupdf.open(stream=data, filetype="pdf")
        for page in doc:
            pix = page.get_pixmap(dpi=200)
            text.append(_ocr_image_bytes(pix.tobytes("png")))
    except Exception:
        return ""
    return "\n".join(text)


def extract_text(data: bytes, filename: str, content_type: str) -> tuple[str, str]:
    """Return (text, method)."""
    name = (filename or "").lower()
    ctype = (content_type or "").lower()
    is_pdf = name.endswith(".pdf") or "pdf" in ctype
    is_img = any(name.endswith(e) for e in (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff")) or ctype.startswith("image/")

    if is_pdf:
        text = ""
        if pdfplumber is not None:
            try:
                with pdfplumber.open(io.BytesIO(data)) as pdf:
                    text = "\n".join((p.extract_text() or "") for p in pdf.pages)
            except Exception:
                text = ""
        if len(text.strip()) >= 40:
            return text, "pdf-text"
        ocr = _ocr_pdf(data)  # scanned PDF fallback
        if ocr.strip():
            return ocr, "pdf-ocr"
        raise ReportError("Could not read text from this PDF. If it is a scan, try a clearer copy.")

    if is_img:
        ocr = _ocr_image_bytes(data)
        if ocr.strip():
            return ocr, "image-ocr"
        raise ReportError("Could not read text from this image. Try a clearer, higher-resolution photo.")

    raise ReportError("Unsupported file type. Upload a PDF or an image (PNG/JPG).")


# --------------------------------------------------------------------------- #
# Parsing
# --------------------------------------------------------------------------- #
_NUM = r"([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?|[0-9]+(?:\.[0-9]+)?)"
_RANGE_RE = re.compile(rf"{_NUM}\s*[-–—to]+\s*{_NUM}")


def _clean_num(s: str) -> float:
    return float(s.replace(",", ""))


def _find_marker(text_lc: str, marker: dict) -> dict | None:
    for alias in sorted(marker["aliases"], key=len, reverse=True):
        pattern = re.compile(re.escape(alias) + r"\b", re.IGNORECASE)
        for m in pattern.finditer(text_lc):
            start, end = m.start(), m.end()
            # exclusion guard (e.g. avoid matching "HDL cholesterol" as total cholesterol)
            prefix = text_lc[max(0, start - 12):start]
            if any(x in prefix for x in marker.get("exclude_prefix", [])):
                continue
            # look at the text just after the alias for the value
            window = text_lc[end:end + 60]
            num_match = re.search(_NUM, window)
            if not num_match:
                continue
            value = _clean_num(num_match.group(1))
            # sanity bound: ignore absurd captures
            if value <= 0 or value > 100000:
                continue
            # try to capture the report's own reference range further along the line
            after_val = window[num_match.end():num_match.end() + 40]
            rng = _RANGE_RE.search(after_val)
            ref_low, ref_high, ref_source = marker["low"], marker["high"], "standard"
            if rng:
                lo, hi = _clean_num(rng.group(1)), _clean_num(rng.group(2))
                if hi > lo and hi < 100000:
                    ref_low, ref_high, ref_source = lo, hi, "report"
            return {"value": value, "ref_low": ref_low, "ref_high": ref_high, "ref_source": ref_source}
    return None


def _status(value: float, low: float, high: float) -> str:
    if value < low:
        return "Low"
    if value > high:
        return "High"
    return "Normal"


def analyze(data: bytes, filename: str, content_type: str) -> dict[str, Any]:
    text, method = extract_text(data, filename, content_type)
    return analyze_text(text, method)


def analyze_text(text: str, method: str = "text") -> dict[str, Any]:
    text_lc = re.sub(r"[ \t]+", " ", text.lower())

    results: list[dict] = []
    for marker in MARKERS:
        found = _find_marker(text_lc, marker)
        if not found:
            continue
        status = _status(found["value"], found["ref_low"], found["ref_high"])
        note = ""
        if status == "High":
            note = marker["high_note"]
        elif status == "Low":
            note = marker["low_note"]
        results.append({
            "key": marker["key"],
            "name": marker["name"],
            "category": marker["category"],
            "value": found["value"],
            "unit": marker["unit"],
            "ref_low": found["ref_low"],
            "ref_high": found["ref_high"],
            "ref_source": found["ref_source"],
            "status": status,
            "about": marker["about"],
            "note": note,
            "advice": marker["advice"] if status != "Normal" else "",
            "related": marker.get("related", ""),
        })

    abnormal = [r for r in results if r["status"] != "Normal"]
    categories: dict[str, list[dict]] = {}
    for r in results:
        categories.setdefault(r["category"], []).append(r)

    related = sorted({r["related"] for r in abnormal if r["related"]})

    if not results:
        summary = ("We could not confidently detect standard lab values in this document. "
                   "It may use an unusual format, or be a type of report this tool does not yet parse.")
    elif not abnormal:
        summary = (f"We detected {len(results)} lab value(s), and all of them fall within their "
                   "normal reference ranges. Keep up your current healthy habits.")
    else:
        names = ", ".join(r["name"] for r in abnormal[:5])
        summary = (f"We detected {len(results)} lab value(s); {len(abnormal)} fall outside the normal "
                   f"reference range: {names}{'…' if len(abnormal) > 5 else ''}. "
                   "See the flagged items below for plain-language explanations and next steps.")

    return {
        "method": method,
        "summary": summary,
        "counts": {"total": len(results), "abnormal": len(abnormal),
                   "normal": len(results) - len(abnormal)},
        "flagged": abnormal,
        "results": results,
        "categories": [{"name": k, "markers": v} for k, v in categories.items()],
        "related_assessments": related,
        "disclaimer": (
            "This analysis is generated automatically from the values detected in your document and "
            "compared to general adult reference ranges, which vary by lab, age, and sex. It is for "
            "educational purposes only, is not a diagnosis, and may miss or misread values. Always "
            "review your report with a qualified healthcare professional."
        ),
    }
