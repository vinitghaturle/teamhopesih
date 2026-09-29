"""Tender Guard - Hardcoding Prevention Verification Test.

Scans the backend codebase to ensure NO test queries, holdout phrases,
or golden dataset literals are hardcoded in source code or configuration files.
"""

import json
from pathlib import Path
import pytest

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
BACKEND_DIR = BASE_DIR / "app" / "backend"
EVAL_DIR = BASE_DIR / "eval"


def test_zero_hardcoded_queries():
    """Ensure no query strings from golden.json or holdout.json appear in app/backend."""
    golden_path = EVAL_DIR / "golden.json"
    holdout_path = EVAL_DIR / "holdout.json"

    queries_to_check = []

    if golden_path.exists():
        with open(golden_path, "r", encoding="utf-8") as f:
            golden_data = json.load(f)
            for item in golden_data:
                q = item.get("query", "").strip()
                if len(q) > 20:
                    queries_to_check.append(q)

    if holdout_path.exists():
        with open(holdout_path, "r", encoding="utf-8") as f:
            holdout_data = json.load(f)
            for item in holdout_data:
                q = item.get("query", "").strip()
                if len(q) > 20:
                    queries_to_check.append(q)

    assert len(queries_to_check) > 0, "No queries found to check."

    # Scan all .py files in backend, excluding test files
    backend_files = list(BACKEND_DIR.glob("**/*.py"))
    
    violations = []

    for f_path in backend_files:
        if "tests" in str(f_path):
            continue
        
        content = f_path.read_text(encoding="utf-8", errors="ignore")
        for q in queries_to_check:
            # Check for substantial substrings (e.g. 30+ chars)
            sub = q[:30].lower()
            if sub in content.lower():
                violations.append((str(f_path), q))

    assert len(violations) == 0, f"Found hardcoded test queries in backend: {violations}"
