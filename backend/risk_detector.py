
def get_items(value):
    """Convert strings, dictionaries or lists into a consistent list."""

    if isinstance(value, list):
        return value

    if isinstance(value, str) and value.strip():
        return [value]

    if isinstance(value, dict):
        return [value]

    return []


def normalize_condition(item, category):
    """Handle both AI-generated strings and dictionaries."""

    if isinstance(item, str):
        return {
            "title": item,
            "description": item,
            "severity": "Low",
            "category": category
        }

    if isinstance(item, dict):
        return {
            "title": str(item.get("title", "Document information")),
            "description": str(
                item.get("description", item.get("title", ""))
            ),
            "severity": (
                item.get("severity", "Low")
                if item.get("severity") in ["Low", "Medium", "High"]
                else "Low"
            ),
            "category": category
        }

    return None


def calculate_risk(analysis):
    """Calculate a safe risk overview from document information."""

    document_type = str(
        analysis.get("document_type", "")
    ).lower()

    # Resumes do not need legal risk detection.
    if "resume" in document_type or "cv" in document_type:
        return {
            "overall_risk": "Not applicable",
            "total_risks": 0,
            "high_risks": 0,
            "medium_risks": 0,
            "low_risks": 0,
            "risks": [],
            "message": "Risk assessment is not applicable to resumes."
        }

    categories = {
        "key_conditions": "Important Conditions",
        "financial_obligations": "Financial Obligations",
        "deadlines": "Deadlines",
        "penalties": "Penalties"
    }

    risks = []

    for field, category in categories.items():

        for item in get_items(analysis.get(field, [])):

            condition = normalize_condition(item, category)

            if condition:
                risks.append(condition)

    high_count = sum(
        1 for item in risks if item["severity"] == "High"
    )

    medium_count = sum(
        1 for item in risks if item["severity"] == "Medium"
    )

    low_count = sum(
        1 for item in risks if item["severity"] == "Low"
    )

    if high_count:
        overall = "High"
    elif medium_count:
        overall = "Medium"
    else:
        overall = "Low"

    return {
        "overall_risk": overall,
        "total_risks": len(risks),
        "high_risks": high_count,
        "medium_risks": medium_count,
        "low_risks": low_count,
        "risks": risks,
        "message": "Review the listed document information carefully."
    }


def add_risk_overview(analysis):
    """Add risk overview without changing the original analysis."""

    if not isinstance(analysis, dict):
        raise ValueError("Invalid document analysis.")

    analysis["risk_overview"] = calculate_risk(analysis)

    return analysis
