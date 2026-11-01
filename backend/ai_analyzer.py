
import os
import json
import re
import time
import urllib.request
import urllib.error

from dotenv import load_dotenv


# ==================================================
# CONFIGURATION - LOAD EXISTING .ENV
# ==================================================

load_dotenv()

OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://localhost:11434/api/chat"
)

MODEL_NAME = os.getenv(
    "OLLAMA_MODEL",
    "llama3.2:1b"
)

TIMEOUT = 240
CHUNK_SIZE = 3500


# ==================================================
# RESULT SCHEMA
# ==================================================

INFORMATION_FIELDS = [
    "names",
    "addresses",
    "education",
    "skills",
    "experience",
    "projects",
    "certifications",
    "achievements",
    "other_details"
]


def string_list(max_items=3):
    return {
        "type": "array",
        "items": {"type": "string"},
        "maxItems": max_items
    }


RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "document_type": {"type": "string"},
        "summary": string_list(3),
        "important_points": string_list(3),
        "extracted_information": {
            "type": "object",
            "properties": {
                field: string_list(3)
                for field in INFORMATION_FIELDS
            },
            "required": INFORMATION_FIELDS,
            "additionalProperties": False
        },
        "tamil_summary": string_list(1),
        "key_conditions": string_list(3),
        "financial_obligations": string_list(3),
        "deadlines": string_list(3),
        "penalties": string_list(3),
        "missing_information": string_list(2),
        "checklist": string_list(2),
        "overall_risk": {
            "type": "string",
            "enum": ["Low", "Medium", "High"]
        },
        "disclaimer": {"type": "string"}
    },
    "required": [
        "document_type",
        "summary",
        "important_points",
        "extracted_information",
        "tamil_summary",
        "key_conditions",
        "financial_obligations",
        "deadlines",
        "penalties",
        "missing_information",
        "checklist",
        "overall_risk",
        "disclaimer"
    ],
    "additionalProperties": False
}


# ==================================================
# COMMON HELPERS
# ==================================================

def empty_result():

    return {
        "document_type": "Unknown",
        "summary": [],
        "important_points": [],
        "key_conditions": [],
        "financial_obligations": [],
        "deadlines": [],
        "penalties": [],
        "missing_information": [],
        "checklist": [],
        "tamil_summary": [],
        "overall_risk": "Low",
        "extracted_information": {
            "names": [],
            "addresses": [],
            "education": [],
            "skills": [],
            "experience": [],
            "projects": [],
            "certifications": [],
            "achievements": [],
            "other_details": [],
            "emails": [],
            "phone_numbers": [],
            "dates": [],
            "amounts": [],
            "websites": []
        },
        "disclaimer": (
            "Verify important information against the original document."
        )
    }


def clean_text(value):
    return value.strip().strip("*").strip()


def add_unique(target, values):

    for value in values:

        if isinstance(value, str) and value.strip():

            value = value.strip()

            if value not in target:
                target.append(value)

    return target


def get_label_value(text, label):

    pattern = (
        rf"(?im)^\s*\*{{0,2}}\s*"
        rf"{re.escape(label)}"
        rf"\s*\*{{0,2}}\s*:\s*(.*?)\s*$"
    )

    match = re.search(pattern, text)

    return clean_text(match.group(1)) if match else None


def matching_sentences(text, keywords, maximum=5):

    parts = re.split(
        r"(?<=[.!?])\s+|\n+",
        text
    )

    found = []

    for part in parts:

        item = clean_text(part)

        if not item:
            continue

        if any(
            keyword.lower() in item.lower()
            for keyword in keywords
        ):

            if item not in found:
                found.append(item)

        if len(found) >= maximum:
            break

    return found


# ==================================================
# CONTACT AND BASIC EXTRACTION
# ==================================================

def extract_document_details(text):

    emails = sorted(set(re.findall(
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
        text
    )))

    websites = sorted(set(re.findall(
        r"(?:https?://|www\.)[^\s<>\"']+",
        text,
        re.IGNORECASE
    )))

    phones = sorted(set(
        re.findall(
            r"(?<!\d)(?:\+\d{1,3}[\s.-]?)?"
            r"(?:\d[\s.-]?){9,12}\d(?!\d)",
            text
        )
    ))

    date_pattern = (
        r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b"
        r"|\b\d{1,2}\s+"
        r"(?:January|February|March|April|May|June|July|August|September|October|November|December)"
        r"\s+\d{4}\b"
        r"|\b(?:January|February|March|April|May|June|July|August|September|October|November|December)"
        r"\s+\d{1,2},?\s+\d{4}\b"
    )

    dates = sorted(set(re.findall(
        date_pattern, text, re.IGNORECASE
    )))

    amount_pattern = (
        r"(?:₹|Rs\.?|INR)\s?[\d,]+(?:\.\d{1,2})?"
        r"|\bUSD\s?[\d,]+(?:\.\d{1,2})?"
    )

    amounts = sorted(set(re.findall(
        amount_pattern, text, re.IGNORECASE
    )))

    return {
        "emails": emails,
        "phone_numbers": phones,
        "websites": websites,
        "dates": dates,
        "amounts": amounts
    }


# ==================================================
# DOCUMENT CLASSIFICATION
# ==================================================

def classify_document(text):

    lower = text.lower()

    rental_words = [
        "rental agreement",
        "residential rental",
        "landlord",
        "tenant",
        "security deposit",
        "monthly rent"
    ]

    offer_words = [
        "offer letter",
        "pleased to offer",
        "internship offer",
        "internship details",
        "joining date",
        "employment offer"
    ]

    rental_count = sum(
        word in lower for word in rental_words
    )

    offer_count = sum(
        word in lower for word in offer_words
    )

    if rental_count >= 2:
        return "rental"

    if offer_count >= 2 and (
        "intern" in lower or "employment" in lower
    ):
        return "internship" if "intern" in lower else "employment"

    subscription_words = [
        "subscription policy",
        "subscription plan",
        "cancellation policy",
        "auto renewal",
        "billing period"
    ]

    subscription_count = sum(
        word in lower for word in subscription_words
    )

    if subscription_count >= 2:
        return "subscription"

    if "resume" in lower or "curriculum vitae" in lower:
        return "resume"

    return "other"


# ==================================================
# DIRECT RENTAL AGREEMENT ANALYSIS
# ==================================================

def analyze_rental_without_ai(text):

    print("CLARIFY AI: Rental agreement detected.")
    print("CLARIFY AI: Using direct extraction.")

    result = empty_result()
    details = result["extracted_information"]

    details.update(extract_document_details(text))

    landlord = get_label_value(text, "Landlord")
    tenant = get_label_value(text, "Tenant")
    address = get_label_value(text, "Property Address")

    if landlord:
        details["names"].append("Landlord: " + landlord)

    if tenant:
        details["names"].append("Tenant: " + tenant)

    if address:
        details["addresses"].append(address)

    rent = matching_sentences(
        text,
        ["monthly rent", "rent of", "rent per month"]
    )

    deposit = matching_sentences(
        text,
        ["security deposit", "refundable deposit"]
    )

    late_charges = matching_sentences(
        text,
        ["late payment charge", "late fee", "late payment penalty"]
    )

    agreement_period = matching_sentences(
        text,
        ["valid for", "agreement period", "rental period"]
    )

    payment_date = matching_sentences(
        text,
        ["on or before", "payment due", "day of every month"]
    )

    notice_period = matching_sentences(
        text,
        ["notice period", "written notice"]
    )

    conditions = matching_sentences(
        text,
        [
            "maintenance",
            "residential purposes",
            "subletting",
            "written permission",
            "normal wear and tear",
            "electricity",
            "water charges"
        ]
    )

    financial = []
    add_unique(financial, rent)
    add_unique(financial, deposit)
    add_unique(financial, late_charges)

    deadlines = []
    add_unique(deadlines, agreement_period)
    add_unique(deadlines, payment_date)
    add_unique(deadlines, notice_period)

    important = []
    add_unique(important, notice_period)
    add_unique(important, conditions)
    add_unique(important, late_charges)

    result["document_type"] = "Residential Rental Agreement"
    result["summary"] = (rent + deposit + agreement_period)[:3]
    result["important_points"] = important[:3]
    result["financial_obligations"] = financial[:5]
    result["deadlines"] = deadlines[:5]
    result["key_conditions"] = (notice_period + conditions)[:5]
    result["penalties"] = late_charges[:3]

    result["tamil_summary"] = [
        "இந்த வாடகை ஒப்பந்தத்தில் வாடகைத் தொகை, முன்பணம், ஒப்பந்த காலம் மற்றும் முக்கிய விதிமுறைகள் பற்றிய விவரங்கள் உள்ளன."
    ]

    result["analysis_coverage"] = {
        "sections_analyzed": 1,
        "total_characters": len(text)
    }

    print("CLARIFY AI: Rental extraction completed.")

    return result


# ==================================================
# DIRECT INTERNSHIP / EMPLOYMENT ANALYSIS
# ==================================================

def analyze_offer_without_ai(text, document_kind):

    print("CLARIFY AI: Offer letter detected.")
    print("CLARIFY AI: Using direct extraction.")

    result = empty_result()
    details = result["extracted_information"]

    details.update(extract_document_details(text))

    recipient = get_label_value(text, "To")
    company = get_label_value(text, "Company")
    position = get_label_value(text, "Position")
    duration = get_label_value(text, "Duration")
    joining_date = get_label_value(text, "Joining Date")
    stipend = get_label_value(text, "Monthly Stipend")
    salary = get_label_value(text, "Salary")
    hr_email = get_label_value(text, "HR Email")
    website = get_label_value(text, "Company Website")

    if not position:

        match = re.search(
            r"position as\s+(.+?)\s+at\s+(.+?)[.,\n]",
            text,
            re.IGNORECASE
        )

        if match:
            position = match.group(1).strip()
            company = company or match.group(2).strip()

    if recipient:
        details["names"].append(recipient)

    if company:
        details["other_details"].append("Company: " + company)

    if position:
        details["experience"].append(position)

    if hr_email:
        add_unique(details["emails"], [hr_email])

    if website:
        add_unique(details["websites"], [website])

    responsibilities = matching_sentences(
        text,
        [
            "develop and test",
            "assist the development",
            "progress reports",
            "team meetings"
        ],
        maximum=4
    )

    conditions = matching_sentences(
        text,
        [
            "confidentiality",
            "weekly progress",
            "completion certificate",
            "written notice",
            "terminate"
        ],
        maximum=4
    )

    financial = []

    if stipend:
        financial.append("Monthly stipend: " + stipend)
    elif salary:
        financial.append("Salary: " + salary)

    summary = []

    if position:
        summary.append("Position: " + position)

    if company:
        summary.append("Company: " + company)

    if duration:
        summary.append("Duration: " + duration)

    if stipend:
        summary.append("Monthly stipend: " + stipend)

    if joining_date:
        summary.append("Joining date: " + joining_date)

    important = []
    add_unique(important, responsibilities)
    add_unique(important, conditions)

    deadlines = []

    if joining_date:
        deadlines.append("Joining date: " + joining_date)

    if duration:
        deadlines.append("Internship duration: " + duration)

    notice = matching_sentences(
        text,
        [
            "days' written notice",
            "days written notice",
            "notice before ending"
        ]
    )

    add_unique(deadlines, notice)

    result["document_type"] = (
        "Internship Offer Letter"
        if document_kind == "internship"
        else "Employment Offer Letter"
    )

    result["summary"] = summary[:3]
    result["important_points"] = important[:3]
    result["financial_obligations"] = financial
    result["deadlines"] = deadlines[:4]
    result["key_conditions"] = conditions[:4]
    result["checklist"] = responsibilities[:2]

    if document_kind == "internship":

        result["tamil_summary"] = [
            "இந்த இன்டர்ன்ஷிப் வாய்ப்பு கடிதத்தில் நிறுவனத்தின் பெயர், பணிப்பதவி, உதவித்தொகை, பணிக்காலம் மற்றும் முக்கிய நிபந்தனைகள் குறிப்பிடப்பட்டுள்ளன."
        ]

    else:

        result["tamil_summary"] = [
            "இந்த வேலைவாய்ப்பு கடிதத்தில் நிறுவனத்தின் பெயர், பணிப்பதவி, சம்பளம் மற்றும் வேலை நிபந்தனைகள் குறிப்பிடப்பட்டுள்ளன."
        ]

    result["analysis_coverage"] = {
        "sections_analyzed": 1,
        "total_characters": len(text)
    }

    return result


# ==================================================
# DOCUMENT CHUNKING
# ==================================================

def split_text(text):

    paragraphs = [
        item.strip()
        for item in text.splitlines()
        if item.strip()
    ]

    chunks = []
    current = ""

    for paragraph in paragraphs:

        while len(paragraph) > CHUNK_SIZE:

            if current:
                chunks.append(current)
                current = ""

            chunks.append(paragraph[:CHUNK_SIZE])
            paragraph = paragraph[CHUNK_SIZE:]

        if len(current) + len(paragraph) + 1 > CHUNK_SIZE:

            if current:
                chunks.append(current)

            current = paragraph

        else:
            current = (current + "\n" + paragraph).strip()

    if current:
        chunks.append(current)

    return chunks or [text[:CHUNK_SIZE]]


# ==================================================
# AI ANALYSIS USING LOCAL OLLAMA ONLY
# ==================================================

def analyze_chunk(chunk, language):

    prompt = f"""
You are CLARIFY AI, an accurate document reader.

Extract facts from the document. Never invent information.

For resumes extract education, skills, experience, projects,
certifications and achievements.

For subscription policies extract service, provider, plan,
price, billing, renewal, cancellation, refunds and restrictions.

For other documents identify the actual type and extract
the relevant facts.

RULES:
- Use English for extracted information.
- Never treat a resume as a legal agreement.
- Never invent amounts, dates, risks or penalties.
- Keep sentences short and factual.
- Leave irrelevant categories empty.
- Leave tamil_summary empty.
- Use strings in arrays, never nested objects.
- Return only JSON matching the supplied schema.

DOCUMENT TEXT:
{chunk}
"""

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "stream": False,
        "format": RESPONSE_SCHEMA,
        "keep_alive": "10m",
        "options": {
            "temperature": 0,
            "num_ctx": 2048,
            "num_predict": 900
        }
    }

    request = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(
            payload,
            ensure_ascii=False
        ).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    started = time.perf_counter()

    try:

        with urllib.request.urlopen(
            request,
            timeout=TIMEOUT
        ) as response:

            result = json.loads(
                response.read().decode("utf-8")
            )

        content = result.get(
            "message", {}
        ).get("content", "")

        print("\n--- OLLAMA PERFORMANCE ---")
        print(
            f"Request time: "
            f"{time.perf_counter() - started:.2f} seconds"
        )
        print("Done reason:", result.get("done_reason"))
        print("Generated tokens:", result.get("eval_count", 0))

        if result.get("eval_duration"):

            generation_seconds = (
                result["eval_duration"] / 1_000_000_000
            )

            print(
                f"Generation time: {generation_seconds:.2f} seconds"
            )

        print("--- END PERFORMANCE ---\n")

        if not content.strip():
            raise RuntimeError("Ollama returned an empty response.")

        try:
            analysis = json.loads(content)

        except json.JSONDecodeError as error:

            print("\n--- INVALID OLLAMA RESPONSE ---")
            print(content[:2000])
            print("Done reason:", result.get("done_reason"))
            print("--- END RESPONSE ---\n")

            raise RuntimeError(
                "Ollama returned incomplete JSON. "
                "Try a shorter document."
            ) from error

        if not isinstance(analysis, dict):
            raise RuntimeError("Invalid AI response structure.")

        return analysis

    except urllib.error.HTTPError as error:

        raise RuntimeError(
            f"Ollama HTTP error: {error.code}"
        ) from error

    except urllib.error.URLError as error:

        raise RuntimeError(
            "Cannot connect to Ollama. Check that Ollama is running."
        ) from error

    except TimeoutError as error:

        raise RuntimeError(
            "AI analysis timed out. Please try again."
        ) from error


# ==================================================
# MERGE AI RESULTS
# ==================================================

def merge_analyses(results):

    merged = empty_result()

    list_fields = [
        "summary",
        "important_points",
        "key_conditions",
        "financial_obligations",
        "deadlines",
        "penalties",
        "missing_information",
        "checklist",
        "tamil_summary"
    ]

    risk_order = {
        "Low": 1,
        "Medium": 2,
        "High": 3
    }

    for result in results:

        if not isinstance(result, dict):
            continue

        if (
            result.get("document_type")
            and merged["document_type"] == "Unknown"
        ):
            merged["document_type"] = result["document_type"]

        risk = result.get("overall_risk", "Low")

        if risk in risk_order:

            if risk_order[risk] > risk_order[merged["overall_risk"]]:
                merged["overall_risk"] = risk

        for field in list_fields:

            values = result.get(field, [])

            if isinstance(values, list):

                add_unique(
                    merged[field],
                    [
                        item for item in values
                        if isinstance(item, str)
                    ]
                )

        extracted = result.get(
            "extracted_information", {}
        )

        if isinstance(extracted, dict):

            for field in INFORMATION_FIELDS:

                values = extracted.get(field, [])

                if isinstance(values, list):

                    add_unique(
                        merged["extracted_information"][field],
                        [
                            item for item in values
                            if isinstance(item, str)
                        ]
                    )

    return merged


# ==================================================
# SUMMARY FALLBACK
# ==================================================

def create_summary_fallback(analysis):

    document_type = str(
        analysis.get("document_type", "")
    ).lower()

    extracted = analysis.get(
        "extracted_information", {}
    )

    if "resume" in document_type or "cv" in document_type:

        source = extracted

        categories = [
            ("Education", "education"),
            ("Skills", "skills"),
            ("Experience", "experience"),
            ("Projects", "projects"),
            ("Certifications", "certifications")
        ]

    else:

        source = analysis

        categories = [
            ("Financial details", "financial_obligations"),
            ("Important conditions", "key_conditions"),
            ("Deadlines", "deadlines"),
            ("Penalties", "penalties")
        ]

    summary = []

    for label, field in categories:

        values = source.get(field, [])

        if isinstance(values, list):

            for value in values[:2]:

                if isinstance(value, str) and value.strip():
                    summary.append(f"{label}: {value}")

                if len(summary) >= 3:
                    return summary

    return summary


def create_tamil_summary(analysis):

    kind = str(
        analysis.get("document_type", "")
    ).lower()

    if "resume" in kind or "cv" in kind:

        return [
            "இந்த Resume-ல் கல்வி, திறன்கள், வேலை அனுபவம், திட்டங்கள் மற்றும் சான்றிதழ்கள் பற்றிய விவரங்கள் உள்ளன."
        ]

    if "rental" in kind:

        return [
            "இந்த வாடகை ஒப்பந்தத்தில் வாடகைத் தொகை, முன்பணம், ஒப்பந்த காலம் மற்றும் முக்கிய விதிமுறைகள் பற்றிய விவரங்கள் உள்ளன."
        ]

    if "internship" in kind:

        return [
            "இந்த இன்டர்ன்ஷிப் கடிதத்தில் நிறுவனத்தின் பெயர், பணிப்பதவி, உதவித்தொகை, பணிக்காலம் மற்றும் முக்கிய நிபந்தனைகள் குறிப்பிடப்பட்டுள்ளன."
        ]

    if "employment" in kind:

        return [
            "இந்த வேலைவாய்ப்பு கடிதத்தில் பணிப்பதவி, சம்பளம், வேலை காலம் மற்றும் முக்கிய நிபந்தனைகள் குறிப்பிடப்பட்டுள்ளன."
        ]

    if "subscription" in kind:

        return [
            "இந்த சந்தா ஆவணத்தில் கட்டணம், புதுப்பித்தல் மற்றும் ரத்து செய்வதற்கான விதிமுறைகள் குறிப்பிடப்பட்டுள்ளன."
        ]

    return [
        "இந்த ஆவணத்தின் முக்கிய விவரங்கள் கீழே தொகுத்து வழங்கப்பட்டுள்ளன."
    ]


# ==================================================
# MAIN DOCUMENT ANALYSIS
# ==================================================

def analyze_document(document_text, language="English"):

    if not document_text or not document_text.strip():
        raise ValueError("No document text was provided.")

    started = time.perf_counter()

    print("\nCLARIFY AI: Preparing document...")

    kind = classify_document(document_text)

    # Rental agreement: direct extraction.
    if kind == "rental":

        analysis = analyze_rental_without_ai(document_text)

        print(
            f"Total analysis time: "
            f"{time.perf_counter() - started:.2f} seconds"
        )

        return analysis

    # Internship and employment: direct extraction.
    if kind in ["internship", "employment"]:

        analysis = analyze_offer_without_ai(
            document_text,
            kind
        )

        print(
            f"Total analysis time: "
            f"{time.perf_counter() - started:.2f} seconds"
        )

        return analysis

    # Resume, subscription and other documents: Ollama.
    details = extract_document_details(document_text)
    chunks = split_text(document_text)

    print(
        f"CLARIFY AI: {len(chunks)} section(s) to analyze."
    )

    results = []

    for index, chunk in enumerate(chunks, start=1):

        print(
            f"CLARIFY AI: Analyzing section {index}/{len(chunks)}..."
        )

        results.append(
            analyze_chunk(chunk, language)
        )

    analysis = merge_analyses(results)

    # Add contact details extracted directly.
    extracted = analysis["extracted_information"]

    for field in [
        "emails",
        "phone_numbers",
        "dates",
        "amounts",
        "websites"
    ]:

        add_unique(extracted[field], details[field])

    # Generate fallback summary if required.
    if not analysis.get("summary"):

        analysis["summary"] = create_summary_fallback(analysis)

    # Use reliable Tamil explanation.
    analysis["tamil_summary"] = create_tamil_summary(analysis)

    # Add coverage and disclaimer.
    analysis["analysis_coverage"] = {
        "sections_analyzed": len(chunks),
        "total_characters": len(document_text)
    }

    analysis["disclaimer"] = (
        "CLARIFY AI extracts and explains information from your document. "
        "Always verify important information against the original document."
    )

    print("\nCLARIFY AI: Analysis completed successfully.")
    print(
        f"Total analysis time: "
        f"{time.perf_counter() - started:.2f} seconds"
    )

    return analysis
