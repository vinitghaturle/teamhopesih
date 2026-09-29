# Tender Guard — AI Indian Standards Recommender for Public Procurement

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Frontend-Next.js%2014-000000.svg)](https://nextjs.org)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB.svg)](https://python.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0%2B-3178C6.svg)](https://www.typescriptlang.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**Tender Guard** is an AI-powered compliance and recommendation platform for Indian Standards (Bureau of Indian Standards — BIS) in public procurement. It analyzes tender technical specifications, extracts explicit and implicit requirements, audits cited standards for obsolescence or version conflicts, performs deterministic quality gap checks, and generates legally enforceable tender clause packs with multi-format export capabilities (DOCX, PDF, Markdown, JSON).

---

## 🚀 Key Capabilities & Features

1. **Hybrid Retrieval Pipeline (Sparse + Dense + Cross-Encoder Reranker)**:
   - BM25Okapi sparse keyword matching for exact technical terms, standard codes, and grades.
   - Dense semantic vector embeddings (`BAAI/bge-small-en-v1.5`) via FAISS.
   - Reciprocal Rank Fusion (RRF) with Cross-Encoder reranking (`cross-encoder/ms-marco-MiniLM-L-6-v2`).
   - Strict post-retrieval relevance floor (-5.0) for zero-hallucination refusal on out-of-scope tenders.

2. **Stale Citation & Superseded Standards Audit**:
   - Automatically detects cited standards (e.g., `IS 456:1978`, `IS 1786:1985`, `IS 8112:1989`).
   - Flags superseded/withdrawn standards and provides immediate transition guidance to valid active editions (e.g., `IS 456:2000`, `IS 1786:2008`).

3. **Citation vs. Requirement Mismatch Detection**:
   - Detects conflicts between tender material qualifiers and cited standard specifications (e.g., `HDPE` pipe specification citing `IS 4985` for uPVC), flagging `CITATION_MISMATCH` with remediation warnings.

4. **Deterministic Specification Gap Analysis**:
   - Cross-examines tender clauses against required testing, sampling, and quality parameters (compressive strength, chemical composition, coating thickness, hydraulic test).
   - Identifies omitted parameters and presents verbatim snippet evidence.

5. **1-Hop Allied Standards Knowledge Graph**:
   - Traverses standard relationships: normative references, test methods, terminology, safety codes, installation practices, and related product specifications.

6. **Legal Clause Pack Generator**:
   - Generates paste-ready contract clauses tailored for procurement officers.
   - Differentiates mandatory QCO compliance clauses for product specifications vs. application guidelines for codes of practice.

7. **Officer Review Workflow & Audit Trail**:
   - Allows procurement officers to Accept, Reject, or Flag recommendations with remarks.
   - Filtered multi-format export (DOCX, PDF, Markdown, JSON) reflecting review decisions.

8. **Multilingual Procurement Engine**:
   - Supports tender inputs in English, Hindi (`hi`), and Marathi (`mr`).
   - Domain-specific procurement translation dictionary and script-aware parsing.

9. **Government Portal Integration Simulation**:
   - Embeddable widget (`/embed`) and interactive GeM simulation portal (`/portal-demo`) showcasing frictionless procurement workflow integration.

---

## 🏛️ System Architecture

```
                                    +-----------------------------+
                                    |     Tender Specification    |
                                    | (Text / PDF / DOCX / Voice) |
                                    +--------------+--------------+
                                                   |
                                                   v
                                    +-----------------------------+
                                    |  Document & Language Parser |
                                    | (pypdf / docx / Multilingual|
                                    +--------------+--------------+
                                                   |
                    +------------------------------+------------------------------+
                    |                                                             |
                    v                                                             v
     +------------------------------+                              +------------------------------+
     |   Hybrid Retrieval Engine    |                              |     Stale Citation Audit     |
     | - Dense (bge-small-en-v1.5)  |                              | - Regex Citation Extractor   |
     | - Sparse (BM25Okapi)         |                              | - Citation Mismatch Checker  |
     | - Cross-Encoder Reranker     |                              | - Status & Transition Matrix |
     | - Qualifier Conflict Filter  |                              +------------------------------+
     | - Relevance Floor (-5.0)     |
     +--------------+---------------+
                    |
                    v
     +------------------------------+
     | 1-Hop Allied Graph Expander  |
     | (Normative, Test, Safety)    |
     +--------------+---------------+
                    |
                    v
     +------------------------------+
     |     Spec Gap & Clause Pack   |
     | - Missing Parameter Checker  |
     | - Standard-Type Clause Block |
     | - Officer Review Persistence |
     | - Multi-Format Exporter      |
     +------------------------------+
```

---

## 🛠️ Technology Stack

- **Backend**: FastAPI, Python 3.10+, SQLAlchemy, SQLite, Pydantic v2
- **NLP / ML**: SentenceTransformers (`BAAI/bge-small-en-v1.5`), Cross-Encoder (`ms-marco-MiniLM-L-6-v2`), FAISS, Rank-BM25
- **Document Processing**: `pypdf`, `python-docx`, `reportlab`
- **Frontend**: Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS, Lucide Icons
- **Testing**: Pytest, HTTPX

---

## ⚡ Quick Start & Installation

### Prerequisites
- **Python 3.10+**
- **Node.js 18+** & **npm**
- **Git**

### 1. Clone the Repository
```bash
git clone https://github.com/vinitghaturle/teamhopesih.git
cd teamhopesih
```

### 2. Backend Setup
```bash
# Navigate to backend directory
cd app/backend

# Create and activate a virtual environment
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Seed the standard database
python scripts/seed_db.py

# Run FastAPI server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Frontend Setup
```bash
# Open a new terminal and navigate to frontend directory
cd app/frontend

# Install dependencies
npm install

# Start Next.js development server
npm run dev
```

### 4. Single-Command Launch (Windows PowerShell)
Alternatively, run the automated launch script from the project root:
```powershell
.\run_app.ps1
```

Once running:
- **Web Application**: `http://localhost:3000`
- **Interactive API Docs (Swagger)**: `http://localhost:8000/docs`
- **Backend Health Check**: `http://localhost:8000/api/health`

---

## 🧪 Testing and Verification

Run backend unit and integration test suite:
```powershell
cd app/backend
pytest tests -v
```

Run automated end-to-end smoke test:
```powershell
python scripts/smoke_test.py
```

---

## 📋 Interactive Verification Scenarios

### Scenario 1: Stale Reference Audit (Civil Engineering)
- **Input Specification**:
  ```text
  The contractor shall supply High Strength Deformed Steel Bars conforming to IS 1786:1985 Grade Fe 415.
  Structural concrete shall be designed in accordance with IS 456:1978.
  ```
- **Outcome**:
  - Recommends active `IS 1786:2008` and `IS 456:2000`.
  - Audits citations: `IS 1786:1985` & `IS 456:1978` flagged as **SUPERSEDED** with replacement guidance.

### Scenario 2: Packaged Drinking Water & Allied Graph
- **Input Specification**:
  ```text
  Procurement of 20-litre packaged drinking water jars for government offices conforming to Indian Standards.
  ```
- **Outcome**:
  - Recommends `IS 14543:2024` (Packaged Drinking Water).
  - Graph expands to `IS 10500:2012` (Drinking water baseline), `IS 13428:2005` (Natural Mineral Water), and `IS 15410:2003` (Plastic packaging).
  - Spec Gap checks evaluate microbiological test requirements and total dissolved solids (TDS).

### Scenario 3: Multilingual Query (Hindi)
- **Input Specification**:
  ```text
  भवन निर्माण के लिए टीएमटी स्टील बार Fe 500 ग्रेड
  ```
- **Outcome**:
  - Automatically identifies Hindi (`hi`), normalizes technical terms, and returns `IS 1786:2008` with bilingual clause export.

### Scenario 4: Out-of-Scope Query (Zero-Hallucination Refusal)
- **Input Specification**:
  ```text
  Cloud server hosting on AWS with 99.99% SLA, Kubernetes orchestration, and ISO 27001 data protection.
  ```
- **Outcome**:
  - Triggered post-retrieval relevance floor refusal (`NO_CONFIDENT_MATCH`).
  - Gracefully refuses with explicit explanation without fabricating non-existent standards.

---

## 📄 License
This project is licensed under the MIT License.
