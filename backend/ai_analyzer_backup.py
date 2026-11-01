
import json
import urllib.request
import urllib.error


# ==============================
# OLLAMA CONFIGURATION
# ==============================

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "llama3.2:3b"


# ==============================
# DOCUMENT ANALYSIS
# ==============================

def analyze_document(document_text, language="English"):

    if not document_text or not document_text.strip():
        raise ValueError("Document text is empty.")

    if len(document_text) > 30000:
        document_text = document_text[:30000]

    prompt = f"""
You are CLARIFY AI, a precise and easy-to-understand document assistant.

Your goal is to help ordinary people understand important document terms
quickly, without making them read another long report.

EXPLANATION LANGUAGE: {language}

STRICT ACCURACY RULES:

1. Use ONLY information explicitly present in the document.
2. Never invent dates, years, amounts, fees, penalties, names or obligations.
3. Copy dates and amounts accurately, including the year and currency.
4. If a date is clearly mentioned, NEVER report it as missing.
5. If the document does not mention something, say "Not specified in the document."
6. Distinguish between missing information and unclear information.
7. Evidence must be an exact quotation from the document.
8. Do not create a risk just because a condition exists.
9. Do not classify normal conditions as high risk without a clear reason.
10. High risk: significant financial loss, severe penalties or major obligations.
11. Medium risk: financial commitments or important unclear conditions.
12. Low risk: ordinary conditions with limited potential impact.
13. Do not provide legal conclusions or claim that a document is invalid.
14. Do not repeat the same condition in multiple sections unnecessarily.
15. Return valid JSON only. No Markdown or text outside JSON.

SHORT AND SIMPLE OUTPUT RULES:

1. Write in simple language suitable for a beginner.
2. Keep the main summary to a maximum of 3 short bullet points.
3. Each condition's details must be 1-2 short sentences.
4. Each why_it_matters explanation must be one short sentence.
5. Financial details must mention only actual amounts and payment terms.
6. Include only important deadlines that are explicitly mentioned.
7. Checklist must contain 3-6 specific actions when supported by the document.
8. Avoid lengthy paragraphs and unnecessary explanations.
9. Do not repeat the same penalty in multiple sections unless necessary.
10. If no relevant information exists, return an empty array.

TAMIL RULES:

1. Use natural, simple, everyday Tamil.
2. Avoid literal or machine-translated Tamil.
3. Preserve dates, amounts and technical terms accurately.
4. Explain the main document in 2-3 short Tamil sentences.
5. Do not add information that is absent from the document.

RISK RULES:

- Assign High, Medium or Low to each important condition.
- Overall risk must reflect the actual conditions identified.
- Do not automatically assign High risk because one condition exists.
- Explain significant risks using document evidence.

DOCUMENT:
{document_text}

Return JSON using EXACTLY this structure:

{{
    "document_type": "Document type",
    "summary": "Short summary with 2-3 bullet points using newline characters",
    "key_conditions": [
        {{
            "title": "Short condition title",
            "details": "One or two short sentences",
            "severity": "High",
            "evidence": "Exact quotation from the document",
            "why_it_matters": "One short sentence explaining the impact"
        }}
    ],
    "financial_obligations": [
        {{
            "title": "Short financial heading",
            "details": "Actual amount and payment terms in one short sentence"
        }}
    ],
    "deadlines": [
        {{
            "title": "Short deadline heading",
            "details": "Exact date and related requirement"
        }}
    ],
    "penalties": [
        {{
            "title": "Short penalty heading",
            "details": "Actual penalty and the condition that triggers it"
        }}
    ],
    "missing_information": [
        {{
            "title": "Information not specified",
            "details": "Clearly state what is not mentioned or remains unclear"
        }}
    ],
    "checklist": [
        "One specific action the user should take"
    ],
    "tamil_summary": "Simple and natural Tamil explanation in 2-3 short sentences",
    "overall_risk": "High",
    "disclaimer": "This is an AI-generated document explanation and not professional legal advice."
}}

Before returning the JSON, verify every date, amount, year and evidence quotation
against the original document.
"""

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are CLARIFY AI. "
                    "Be accurate, concise and factual. "
                    "Return valid structured JSON only."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "format": "json",
        "stream": False,
        "options": {
            "temperature": 0.1
        }
    }

    try:

        request_data = json.dumps(payload).encode("utf-8")

        req = urllib.request.Request(
            OLLAMA_URL,
            data=request_data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=240) as response:
            result = json.loads(response.read().decode("utf-8"))

        ai_response = result.get("message", {}).get("content", "")

        if not ai_response:
            raise RuntimeError("Ollama returned an empty response.")

        analysis = json.loads(ai_response)

        required_fields = [
            "document_type",
            "summary",
            "key_conditions",
            "financial_obligations",
            "deadlines",
            "penalties",
            "missing_information",
            "checklist",
            "tamil_summary",
            "overall_risk",
            "disclaimer"
        ]

        for field in required_fields:
            if field not in analysis:
                raise ValueError(
                    f"AI response is missing the field: {field}"
                )

        # Validate important response structures.
        list_fields = [
            "key_conditions",
            "financial_obligations",
            "deadlines",
            "penalties",
            "missing_information",
            "checklist"
        ]

        for field in list_fields:
            if not isinstance(analysis[field], list):
                raise ValueError(
                    f"AI response field '{field}' must be a list."
                )

        # Prevent invalid overall risk labels.
        if analysis["overall_risk"] not in ["High", "Medium", "Low"]:
            analysis["overall_risk"] = "Medium"

        return analysis

    except urllib.error.URLError as error:
        raise RuntimeError(
            "Cannot connect to Ollama. Make sure Ollama is running. Details: "
            + str(error)
        )

    except json.JSONDecodeError:
        raise RuntimeError(
            "Ollama returned an invalid JSON response. Please try again."
        )

    except TimeoutError:
        raise RuntimeError(
            "AI analysis timed out. Please try again."
        )

    except Exception as error:
        raise RuntimeError(
            f"Ollama analysis failed: {error}"
        )
