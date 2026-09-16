"""Extract and summarize uploaded medical reports safely."""
from __future__ import annotations

import io
from pathlib import Path

import pdfplumber
import pytesseract
from PIL import Image, UnidentifiedImageError

from core.llm_client import call_llm


MAX_REPORT_BYTES = 10 * 1024 * 1024

MEDICAL_REPORT_SYSTEM_PROMPT = """You are a careful medical report explainer.
Analyze only the report text provided by the user. Do not diagnose, prescribe,
promise a cure, or replace a clinician. Explain medical terms in plain language.
Separate documented findings from uncertainty. If the report has no concerning
abnormal findings, say so clearly and include a brief reassuring message.
If there may be an urgent issue, say to contact a doctor or emergency service
promptly. Recommend discussing every abnormal finding with the appropriate
licensed clinician.

Return valid JSON with exactly these keys:
{
  "summary": "plain-language overview",
  "findings": [{"item": "finding", "meaning": "plain-language meaning", "severity": "normal|watch|urgent"}],
  "next_steps": ["safe, practical next step"],
  "reassurance": "happy/reassuring message when no concerning finding is identified",
  "disclaimer": "brief medical disclaimer"
}
"""


def extract_medical_report_text(file_bytes: bytes, filename: str) -> str:
    if not file_bytes:
        raise ValueError("Uploaded medical report is empty.")
    if len(file_bytes) > MAX_REPORT_BYTES:
        raise ValueError("Medical report must be 10 MB or smaller.")
    suffix = Path(filename).suffix.lower()
    supported_images = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}
    if suffix not in {".pdf", *supported_images}:
        raise ValueError("Upload a PDF or image medical report (JPG, PNG, WEBP, BMP, or TIFF).")

    try:
        if suffix == ".pdf":
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                text = "\n".join(
                    page_text
                    for page in pdf.pages
                    if (page_text := page.extract_text())
                ).strip()
        else:
            with Image.open(io.BytesIO(file_bytes)) as image:
                text = pytesseract.image_to_string(image).strip()
    except UnidentifiedImageError as exc:
        raise ValueError("Could not read this medical report image.") from exc
    except pytesseract.TesseractNotFoundError as exc:
        raise ValueError("Image OCR is unavailable on the server. Install Tesseract OCR and try again.") from exc
    except Exception as exc:
        raise ValueError("Could not read this PDF medical report.") from exc

    if not text:
        raise ValueError(
            "No readable text was found. Use a clearer image or an OCR-processed PDF."
        )
    return text


def analyze_medical_report(text: str) -> dict:
    response = call_llm(
        MEDICAL_REPORT_SYSTEM_PROMPT,
        f"Medical report text:\n\n{text[:50000]}",
        temperature=0.1,
        max_tokens=1600,
    )
    if response.get("error") and not response.get("summary"):
        return {
            "summary": "The report text was extracted, but an automated explanation is temporarily unavailable.",
            "findings": [],
            "next_steps": ["Discuss the report with the clinician who ordered the test."],
            "reassurance": "Keep the original report and arrange a clinician review.",
            "disclaimer": "This is not a diagnosis or a substitute for medical care.",
            "analysis_available": False,
        }

    response.setdefault("findings", [])
    response.setdefault("next_steps", ["Discuss the report with the clinician who ordered the test."])
    response.setdefault("reassurance", "No concerning finding was identified in the explanation.")
    response.setdefault("disclaimer", "This is not a diagnosis or a substitute for medical care.")
    response["analysis_available"] = True
    return response