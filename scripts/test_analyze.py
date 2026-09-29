import sys
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent / "app" / "backend"
sys.path.insert(0, str(BASE_DIR))

from database import SessionLocal
from services.pipeline_service import TenderPipelineService

db = SessionLocal()
service = TenderPipelineService(db)

with open(BASE_DIR / "data" / "sample_tenders" / "construction_tender.txt", "r", encoding="utf-8") as f:
    text = f.read()

res = service.analyze_tender(raw_text=text)
print("TOTAL REQS:", len(res["requirements"]))
for req in res["requirements"]:
    print(f"REQ {req['id']}: [{req['status']}] {req['clause_text'][:60]}")
    for m in req["matched_standards"]:
        print(f"   -> {m['standard_number']} ({m['full_title'][:50]})")

print("\nBILL OF STANDARDS:")
for s in res["bill_of_standards"]:
    print(f" - {s['standard_number']} (Refs: {len(s['referenced_by_requirements'])})")
