"""
extract_fields.py
-----------------
Extracts specific fields from a Cardinal Health Purchase Order PDF
using a FREE local Ollama model (no API key needed).

Requirements:
    pip install pdfplumber watchdog ollama
    Install Ollama: https://ollama.com/download
    Pull a model:   ollama pull llama3.2   (or mistral, gemma2, etc.)
"""

import os
import re
import json
import pdfplumber
import ollama
from pathlib import Path
from datetime import datetime

# ─────────────────────────────────────────────────────────────
#  CONFIGURE: edit fields here anytime — plain English labels
# ─────────────────────────────────────────────────────────────
FIELDS_TO_EXTRACT = [
    "P.O. No.",
    "Date",
    "Buyer",
    "Currency",
    "P.O. value",
    "Supplier No.",
    "Ship From - Company",
    "Ship From - Address",
    "Ship From - City",
    "Ship From - State",
    "Ship From - ZIP",
    "Ship To - Company",
    "Ship To - Address",
    "Ship To - City",
    "Ship To - State",
    "Ship To - ZIP",
    "Ship To - Plant",
    "Sales Order",
    "Customer P.O.",
    "Line Items",   # pulls the full line-item table
]

OLLAMA_MODEL  = "llama3.2"   # change to: mistral, gemma2, phi3, etc.
WATCH_FOLDER  = "./inbox"    # drop PDFs here
OUTPUT_FOLDER = "./output"   # extracted .txt files appear here
# ─────────────────────────────────────────────────────────────


SYSTEM_PROMPT = """You are a precise data extraction assistant.
You will receive raw text from a Cardinal Health Purchase Order PDF.
Extract ONLY the requested fields and return them as a single valid JSON object.

Rules:
- Return ONLY raw JSON. No markdown, no code fences, no explanation.
- If a field is not found, use null.
- For "Line Items", return an array of objects with keys:
  line_no, supplier_material_no, gtin, cardinal_material_no,
  description, to_arrive_by_date, quantity, unit, price, extended_price
- Keep values exactly as they appear in the document.
"""


def extract_text_from_pdf(pdf_path: str) -> str:
    text_parts = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text(layout=True)
            if page_text:
                text_parts.append(page_text)
            for table in page.extract_tables():
                for row in table:
                    if row:
                        text_parts.append(" | ".join(str(c or "").strip() for c in row))
    return "\n".join(text_parts)


def call_ollama(pdf_text: str, fields: list) -> dict:
    fields_list = "\n".join(f"- {f}" for f in fields)
    user_msg = f"""Extract the following fields from this Purchase Order:

{fields_list}

--- PDF TEXT START ---
{pdf_text}
--- PDF TEXT END ---

Return a JSON object with exactly these field names as keys."""

    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_msg},
        ],
        options={"temperature": 0}   # deterministic output
    )

    raw = response["message"]["content"].strip()
    # Strip markdown fences if the model added them anyway
    raw = re.sub(r"^```(?:json)?", "", raw).strip()
    raw = re.sub(r"```$",          "", raw).strip()

    # Find the JSON object even if there's surrounding text
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON found in model response:\n{raw}")
    return json.loads(match.group())


def format_output(data: dict, source_filename: str) -> str:
    lines = []
    lines.append(f"EXTRACTED FIELDS FROM: {source_filename}")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 60)
    lines.append("")

    for key, value in data.items():
        if key == "Line Items" and isinstance(value, list):
            lines.append("LINE ITEMS:")
            lines.append("-" * 60)
            for i, item in enumerate(value, 1):
                lines.append(f"  Item {i}:")
                for k, v in item.items():
                    lines.append(f"    {k}: {v}")
                lines.append("")
        else:
            lines.append(f"{key}: {value}")

    return "\n".join(lines)


def process_pdf(pdf_path: str):
    pdf_path = Path(pdf_path)
    print(f"[+] Processing: {pdf_path.name}")

    pdf_text  = extract_text_from_pdf(str(pdf_path))
    extracted = call_ollama(pdf_text, FIELDS_TO_EXTRACT)
    output    = format_output(extracted, pdf_path.name)

    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    out_path = Path(OUTPUT_FOLDER) / (pdf_path.stem + "_extracted.txt")
    out_path.write_text(output, encoding="utf-8")

    print(f"[✓] Saved → {out_path}")
    return str(out_path)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python extract_fields.py <path_to_pdf>")
        sys.exit(1)
    process_pdf(sys.argv[1])
