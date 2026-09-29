"""Generate full JSON output for the 3 sample tenders."""

import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent / "app" / "backend"
sys.path.insert(0, str(BASE_DIR))

from database import SessionLocal
from services.pipeline_service import TenderPipelineService

db = SessionLocal()
pipeline = TenderPipelineService(db)

SAMPLE_DIR = BASE_DIR / "data" / "sample_tenders"
tenders = [
    ("Construction Tender", SAMPLE_DIR / "construction_tender.txt"),
    ("Water Supply Tender", SAMPLE_DIR / "water_supply_tender.txt"),
    ("Electrical Tender", SAMPLE_DIR / "electrical_tender.txt"),
    ("Stale Citation Construction Tender", SAMPLE_DIR / "stale_construction_tender.txt"),
]

outputs = {}

for name, path in tenders:
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    res = pipeline.analyze_tender(raw_text=text, filename=path.name)
    outputs[name] = res

OUT_FILE = Path(__file__).resolve().parent.parent / "eval" / "sample_tender_analyses.json"
with open(OUT_FILE, "w", encoding="utf-8") as f:
    json.dump(outputs, f, indent=2)

print("Saved sample tender analyses to", OUT_FILE)
