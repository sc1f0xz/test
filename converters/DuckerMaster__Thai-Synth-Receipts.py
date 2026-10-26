"""DuckerMaster/Thai-Synth-Receipts (MIT): synthetic Thai receipts/invoices; every field is gold + OCR boxes.
VLM task: image -> structured JSON extraction. Content stays plain text; the image reference goes to
meta.images (load from the repo's train/clean/images/<sample_id>.*) and common.multimodal_messages() turns it
into the content-list form Qwen3.5 needs (a literal "<image>" string is NOT an image for Qwen3.5). Gold = field dict
(compare with verifiers.json_schema.extract_json + per-field equality).
"""
import ast
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa: E402,F401,F403

SRC = "DuckerMaster/Thai-Synth-Receipts"
FIELDS = ["doc_type", "merchant_name", "merchant_tax_id", "merchant_address", "merchant_phone", "date", "time",
          "items", "subtotal", "discount", "vatable", "tax", "vat_7", "vat_exempt", "total", "currency",
          "invoice_number", "customer_name", "customer_tax_id", "customer_address"]
PROMPT = "สกัดข้อมูลจากเอกสารนี้เป็น JSON ตามฟิลด์: " + ", ".join(FIELDS)


def convert(row):
    gold = {k: row.get(k) for k in FIELDS if k in row}
    rec = record([{"role": "user", "content": PROMPT}], None, f"{SRC}#{row.get('sample_id')}", {"fields": gold})
    rec["meta"] = {"images": [row.get("sample_id")], "ocr_boxes": len(row.get("ocr_boxes") or [])}
    return rec


if __name__ == "__main__":
    main(convert)
