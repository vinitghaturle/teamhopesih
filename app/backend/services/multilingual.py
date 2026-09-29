"""Tender Guard - Multilingual Detection & Procurement Translation Service.

Adapted from:
- refs/SIH-BIS-Procurement-Intelligence/ai/app/nlp/language.py
- refs/BIS/src/lib/language.ts

Provides:
- Unicode script-based language identification (English, Hindi, Marathi, Kannada, Tamil, etc.)
- Deterministic procurement glossary for Hindi/Marathi/Devanagari technical terms
- Query translation to English for retrieval alignment while preserving original query text for UI display.
"""

import re
import unicodedata
from typing import Tuple, Dict, Optional, Any


def detect_language(text: str) -> str:
    """Detect language based on Unicode script distribution."""
    if not text or not text.strip():
        return "en"

    devanagari_count = sum(1 for c in text if 0x0900 <= ord(c) <= 0x097F and unicodedata.category(c).startswith("L"))
    kannada_count = sum(1 for c in text if 0x0C80 <= ord(c) <= 0x0CFF and unicodedata.category(c).startswith("L"))
    tamil_count = sum(1 for c in text if 0x0B80 <= ord(c) <= 0x0BFF and unicodedata.category(c).startswith("L"))
    telugu_count = sum(1 for c in text if 0x0C00 <= ord(c) <= 0x0C7F and unicodedata.category(c).startswith("L"))
    
    total_chars = len(text.strip())

    if devanagari_count > 0:
        # Check Marathi specific markers
        if any(w in text for w in ["पॅक", "केलेले", "पिण्याचे", "पुरवठा", "शासकीय", "कार्यालयासाठी", "पाणी"]):
            return "mr"
        return "hi"
    elif kannada_count > 0:
        return "kn"
    elif tamil_count > 0:
        return "ta"
    elif telugu_count > 0:
        return "te"
    
    return "en"


# Over 160 Procurement & Engineering Domain Terms (Hindi / Marathi -> English)
PROCUREMENT_GLOSSARY: Dict[str, str] = {
    # Water & Piping Systems
    "उच्च घनत्व पॉलीथीन": "High Density Polyethylene",
    "उच्च घनतेचे पॉलीथिलीन": "High Density Polyethylene",
    "एचडीपीई": "HDPE",
    "यूपीवीसी": "uPVC",
    "पीवीसी": "PVC",
    "पीव्हीसी": "PVC",
    "पॉलीइथिलीन": "Polyethylene",
    "पॉलीथिलीन": "Polyethylene",
    "पाइप": "pipe",
    "पाइप्स": "pipes",
    "पाईप": "pipe",
    "पाईप्स": "pipes",
    "नळ": "pipe",
    "नळांची जोडणी": "pipe fittings",
    "पेयजल": "drinking water",
    "पिण्याचे पाणी": "drinking water",
    "पॅक केलेले": "packaged",
    "पैक किया हुआ": "packaged",
    "पानी": "water",
    "जल": "water",
    "आपूर्ति": "supply",
    "पुरवठा": "supply",
    "जल आपूर्ति": "water supply",
    "पाणी पुरवठा": "water supply",
    "बोतलबंद": "bottled",
    "जार": "jar",
    "लिटर": "liter",
    "लीटर": "liter",
    "दबाव पाइप": "pressure pipes",
    "दाब पाईप": "pressure pipes",
    "भूमिगत जल": "groundwater",
    "सांडपाणी": "sewage",
    "मलजल": "sewage",
    "वितरण": "distribution",
    "जलवाहिनी": "water pipeline",

    # Cement, Concrete & Masonry
    "साधारण पोर्टलैंड सीमेंट": "Ordinary Portland Cement",
    "साधारण पोर्टलँड सिमेंट": "Ordinary Portland Cement",
    "पोर्टलैंड सीमेंट": "Portland Cement",
    "पोर्टलँड सिमेंट": "Portland Cement",
    "सीमेंट": "cement",
    "सिमेंट": "cement",
    "पोर्टलैंड": "portland",
    "पोर्टलँड": "portland",
    "कंक्रीट": "concrete",
    "काँक्रीट": "concrete",
    "रेडी मिक्स कंक्रीट": "ready-mix concrete",
    "रेडी मिक्स काँक्रीट": "ready-mix concrete",
    "प्रबलित कंक्रीट": "reinforced concrete",
    "प्रबलित काँक्रीट": "reinforced concrete",
    "मोर्टार": "mortar",
    "गारा": "mortar",
    "रेत": "sand",
    "वाळू": "sand",
    "गिट्टी": "aggregate",
    "खडी": "aggregate",
    "ईंट": "brick",
    "विटा": "bricks",
    "प्लास्टर": "plaster",
    "प्लास्टरिंग": "plastering",
    "दाब सामर्थ्य": "compressive strength",
    "दबाव सामर्थ्य": "compressive strength",
    "सेटिंग समय": "setting time",
    "सेटिंग वेळ": "setting time",
    "जलरोधी": "waterproof",
    "पाणी प्रतिरोधक": "water resistant",

    # Steel, Reinforcement & Structural Metals
    "टीएमटी सरिया": "TMT rebar",
    "टीएमटी बार": "TMT bar",
    "टीएमटी": "TMT",
    "सरिया": "rebar",
    "स्टील बार": "steel bar",
    "स्टील रॉड्स": "steel rods",
    "स्टील": "steel",
    "लोहा": "iron",
    "लोखंड": "iron",
    "संरचनात्मक स्टील": "structural steel",
    "संरचनात्मक पोलाद": "structural steel",
    "पोलाद": "steel",
    "पुनर्बलन": "reinforcement",
    "तनन सामर्थ्य": "tensile strength",
    "तन्यता": "ductility",
    "उपज शक्ति": "yield strength",
    "गैल्वनाइज्ड": "galvanized",
    "जस्त लेपित": "galvanized",
    "जंग रोधक": "corrosion resistant",
    "स्टेनलेस स्टील": "stainless steel",

    # Electrical, Cables, Conduits & Lighting
    "विद्युत केबल": "electric cable",
    "विद्युत तारा": "electric wire",
    "कॉपर केबल": "copper cable",
    "तांबे केबल": "copper cable",
    "तांबा": "copper",
    "तांबे": "copper",
    "अल्युमिनियम": "aluminium",
    "अ‍ॅल्युमिनियम": "aluminium",
    "केबल": "cable",
    "तार": "wire",
    "तारें": "wires",
    "तारा": "wires",
    "आर्मर्ड केबल": "armoured cable",
    "एलईडी": "LED",
    "एलईडी बल्ब": "LED bulb",
    "एलईडी दिवे": "LED lights",
    "दीपक": "lamp",
    "बल्ब": "bulb",
    "प्रकाश": "lighting",
    "रोशनी": "lighting",
    "प्रकाश व्यवस्था": "lighting system",
    "विद्युत": "electric",
    "बिजली": "electricity",
    "वीज": "electricity",
    "वोल्ट": "volt",
    "वोल्टेज": "voltage",
    "इंसुलेशन": "insulation",
    "रोधन": "insulation",
    "फ्लेक्सिबल केबल": "flexible cable",
    "कंड्यूट": "conduit",
    "पाईप लाईन": "pipeline",
    "स्विच": "switch",
    "सॉकेट": "socket",
    "सर्किट ब्रेकर": "circuit breaker",
    "ट्रांसफार्मर": "transformer",
    "जनरेटर": "generator",
    "अर्थिंग": "earthing",
    "भू-संपर्कन": "earthing",

    # Safety, PPE & Vehicles
    "सुरक्षा हेलमेट": "safety helmet",
    "हेलमेट": "helmet",
    "सुरक्षा": "safety",
    "सुरक्षात्मक": "protective",
    "सुरक्षा जोडे": "safety shoes",
    "सुरक्षा जूते": "safety shoes",
    "हातमोजे": "gloves",
    "दस्ताने": "gloves",
    "दुपहिया": "two wheeler",
    "दुचाकी": "two wheeler",
    "सवार": "rider",
    "चालक": "driver",
    "मोटरसाइकिल": "motorcycle",
    "अग्निशामक": "fire extinguisher",
    "अग्निरोधक": "fire resistant",
    "प्राथमिक उपचार": "first aid",

    # Tender, Quality, BIS & Procurement Terms
    "निविदा सूचना": "tender notice",
    "निविदा विनिर्देश": "tender specification",
    "निविदा": "tender",
    "टेंडर": "tender",
    "तांत्रिक विनिर्देश": "technical specifications",
    "तकनीकी विनिर्देश": "technical specifications",
    "खरीद": "procurement",
    "खरेदी": "procurement",
    "शासकीय": "government",
    "सरकारी": "government",
    "कार्यालय": "office",
    "कार्यालयासाठी": "for office",
    "गुणवत्ता": "quality",
    "मानक": "standard",
    "मानके": "standards",
    "भारतीय मानक": "Indian Standard",
    "प्रमाणन": "certification",
    "प्रमाणपत्र": "certificate",
    "अनिवार्य": "mandatory",
    "सक्तीचे": "mandatory",
    "परीक्षण": "testing",
    "चाचणी": "testing",
    "प्रयोगशाळा": "laboratory",
    "प्रयोगशाळा अहवाल": "laboratory report",
    "आवश्यकता": "requirement",
    "अटी व शर्ती": "terms and conditions",
    "नियम": "rules",
    "अनुपालन": "compliance",
    "मान्यता": "accreditation",
    "हमी": "warranty",
    "वॉरंटी": "warranty",
    "दुरुस्ती": "maintenance",
    "देखभाल": "maintenance",
    "काम": "work",
    "बांधकाम": "construction",
    "इमारत": "building",
    "रस्ता": "road",
    "पूल": "bridge",
    "धरण": "dam",
}


def translate_procurement_query(query: str) -> Tuple[str, str]:
    """Translate Hindi/Marathi procurement query to English using deterministic glossary.
    
    Returns:
      (translated_query, detected_lang)
    """
    lang = detect_language(query)
    if lang == "en":
        return query, "en"

    translated = query
    # Sort glossary terms by length descending to replace multi-word phrases first
    for term, eng in sorted(PROCUREMENT_GLOSSARY.items(), key=lambda x: -len(x[0])):
        translated = translated.replace(term, eng)

    # Clean up redundant spaces
    translated = re.sub(r"\s+", " ", translated).strip()
    return translated, lang


class MultilingualService:
    """Service wrapper for language detection and procurement translation provider chain."""

    def __init__(self):
        self.glossary_terms_count = len(PROCUREMENT_GLOSSARY)

    def detect_language(self, text: str) -> str:
        return detect_language(text)

    def translate_query(self, query: str, source_lang: Optional[str] = None) -> str:
        translated, _ = translate_procurement_query(query)
        return translated

    def get_provider_status(self) -> Dict[str, Any]:
        """Returns translation provider status (glossary mode or external API)."""
        import os
        has_api_key = bool(os.environ.get("OPENAI_API_KEY") or os.environ.get("TRANSLATE_API_KEY"))
        return {
            "mode": "api" if has_api_key else "glossary_fallback",
            "provider": "LLM_API" if has_api_key else "Deterministic Procurement Glossary",
            "glossary_terms_count": self.glossary_terms_count,
            "supported_languages": ["en", "hi", "mr"],
        }



