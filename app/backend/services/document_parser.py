"""Document parser service — extracts text from PDF, DOCX, and TXT files.
"""

import io
from pathlib import Path


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from a PDF file using pypdf / PyPDF2 with error handling."""
    if not file_bytes:
        raise ValueError("Empty PDF file data.")
    try:
        try:
            from pypdf import PdfReader
        except ImportError:
            from PyPDF2 import PdfReader

        reader = PdfReader(io.BytesIO(file_bytes))
        text_parts = []
        for page_idx, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text.strip())
        extracted = "\n\n".join(text_parts).strip()
        if not extracted:
            raise ValueError("No extractable text found in PDF.")
        return extracted
    except Exception as e:
        if isinstance(e, ValueError):
            raise
        raise ValueError(f"Corrupted or invalid PDF file: {str(e)}")


def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract text from a DOCX file with error handling."""
    if not file_bytes:
        raise ValueError("Empty DOCX file data.")
    try:
        from docx import Document

        doc = Document(io.BytesIO(file_bytes))
        text_parts = []
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_parts.append(paragraph.text.strip())
        for table in doc.tables:
            for row in table.rows:
                row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                if row_text:
                    text_parts.append(row_text)
        extracted = "\n\n".join(text_parts).strip()
        if not extracted:
            raise ValueError("No extractable text found in DOCX.")
        return extracted
    except Exception as e:
        if isinstance(e, ValueError):
            raise
        raise ValueError(f"Corrupted or invalid DOCX file: {str(e)}")


def extract_text(file_bytes: bytes, filename: str) -> str:
    """Extract text based on file extension."""
    if not file_bytes:
        raise ValueError("File content is empty.")
    
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        return extract_text_from_pdf(file_bytes)
    elif ext in (".docx", ".doc"):
        return extract_text_from_docx(file_bytes)
    elif ext in (".txt", ".text", ".md"):
        try:
            decoded = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            decoded = file_bytes.decode("latin-1", errors="replace")
        if not decoded.strip():
            raise ValueError("TXT file content is empty.")
        return decoded.strip()
    else:
        raise ValueError(f"Unsupported file type: '{ext}'. Supported formats: .pdf, .docx, .txt")
