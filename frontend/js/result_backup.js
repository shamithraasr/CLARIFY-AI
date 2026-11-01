
document.addEventListener("DOMContentLoaded", () => {

    // Get saved AI analysis.
    const savedAnalysis = sessionStorage.getItem("clarifyAnalysis");

    if (!savedAnalysis) {
        document.querySelector(".results-container").innerHTML = `
            <section class="result-card">
                <h2>No Analysis Found</h2>
                <p>Please analyse a document before opening this page.</p>
                <a href="/dashboard" class="primary-button">Go to Dashboard →</a>
            </section>
        `;
        return;
    }

    let analysis;

    try {
        analysis = JSON.parse(savedAnalysis);
    } catch (error) {
        console.error("Unable to read analysis:", error);
        return;
    }

    // Safely display text.
    function setText(id, value, fallback = "No information available.") {
        const element = document.getElementById(id);

        if (!element) return;

        if (value === null || value === undefined || value === "") {
            element.textContent = fallback;
        } else {
            element.textContent = String(value);
        }
    }

    // Convert a value into readable text.
    function getItemText(item) {
        if (typeof item === "string") return item;

        if (typeof item === "number") return String(item);

        if (item && typeof item === "object") {
            return item.details || item.description || item.title ||
                item.condition || item.name || JSON.stringify(item);
        }

        return "No details available.";
    }

    // Display a list safely without inserting HTML from AI.
    function displayList(elementId, items, emptyMessage) {

        const container = document.getElementById(elementId);

        if (!container) return;

        container.replaceChildren();

        if (!Array.isArray(items) || items.length === 0) {
            const empty = document.createElement("p");
            empty.textContent = emptyMessage;
            container.appendChild(empty);
            return;
        }

        items.forEach((item) => {

            const card = document.createElement("div");
            card.className = "result-item";

            if (typeof item === "object" && item !== null) {

                const title = document.createElement("h3");
                title.textContent = item.title || item.name || item.condition || "Details";
                card.appendChild(title);

                const details = document.createElement("p");
                details.textContent = getItemText(item);
                card.appendChild(details);

                if (item.severity) {
                    const severity = document.createElement("span");
                    severity.className = "severity-tag " +
                        String(item.severity).toLowerCase();
                    severity.textContent = String(item.severity) + " Risk";
                    card.appendChild(severity);
                }

                if (item.evidence) {
                    const evidence = document.createElement("p");
                    evidence.className = "evidence-text";
                    evidence.textContent = "Document Evidence: " + item.evidence;
                    card.appendChild(evidence);
                }

                if (item.why_it_matters) {
                    const reason = document.createElement("p");
                    reason.textContent = "Why it matters: " + item.why_it_matters;
                    card.appendChild(reason);
                }

            } else {
                const text = document.createElement("p");
                text.textContent = getItemText(item);
                card.appendChild(text);
            }

            container.appendChild(card);
        });
    }

    // 1. Document summary.
    setText("documentType", analysis.document_type, "Document Analysis");
    setText("documentSummary", analysis.summary);

    // 2. Risk overview.
    const risk = analysis.risk_overview || {};

    const highCount = risk.high_count ?? risk.high ?? 0;
    const mediumCount = risk.medium_count ?? risk.medium ?? 0;
    const lowCount = risk.low_count ?? risk.low ?? 0;

    setText("highRiskCount", highCount, "0");
    setText("mediumRiskCount", mediumCount, "0");
    setText("lowRiskCount", lowCount, "0");

    setText(
        "overallRisk",
        risk.overall_risk || analysis.overall_risk,
        "Not Available"
    );

    // 3. Important conditions.
    displayList(
        "conditionsList",
        analysis.key_conditions,
        "No important conditions were identified."
    );

    // 4. Financial obligations.
    displayList(
        "financialList",
        analysis.financial_obligations,
        "No financial obligations were identified."
    );

    // 5. Deadlines.
    displayList(
        "deadlinesList",
        analysis.deadlines,
        "No specific deadlines were identified."
    );

    // 6. Penalties.
    displayList(
        "penaltiesList",
        analysis.penalties,
        "No penalties were identified."
    );

    // 7. Missing information.
    displayList(
        "missingList",
        analysis.missing_information,
        "No missing information was identified."
    );

    // 8. Tamil explanation.
    setText(
        "tamilSummary",
        analysis.tamil_summary,
        "தமிழ் விளக்கம் கிடைக்கவில்லை."
    );

    // 9. Action checklist.
    const checklistContainer = document.getElementById("checklistList");

    if (checklistContainer) {

        checklistContainer.replaceChildren();

        if (Array.isArray(analysis.checklist) && analysis.checklist.length > 0) {

            analysis.checklist.forEach((item) => {

                const label = document.createElement("label");
                label.className = "checklist-item";

                const checkbox = document.createElement("input");
                checkbox.type = "checkbox";

                const text = document.createElement("span");
                text.textContent = getItemText(item);

                label.appendChild(checkbox);
                label.appendChild(text);

                checklistContainer.appendChild(label);
            });

        } else {
            checklistContainer.textContent = "No action items available.";
        }
    }

    // 10. Disclaimer.
    setText(
        "disclaimer",
        analysis.disclaimer,
        "CLARIFY AI provides document understanding assistance and does not replace professional legal advice."
    );

    console.log("CLARIFY AI results loaded successfully.");
});
