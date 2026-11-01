
document.addEventListener("DOMContentLoaded", () => {

    // Load document analysis
    const savedAnalysis = sessionStorage.getItem("clarifyAnalysis");

    const resultsContainer = document.querySelector(".results-container");

    if (!savedAnalysis) {
        if (resultsContainer) {
            resultsContainer.innerHTML = `
                <section class="result-card">
                    <h2>No Document Found</h2>
                    <p>Please upload and analyse a document first.</p>
                    <a href="/dashboard" class="primary-button">
                        Go to Dashboard
                    </a>
                </section>
            `;
        }
        return;
    }

    let analysis;

    try {
        analysis = JSON.parse(savedAnalysis);
    } catch (error) {
        console.error("Unable to read analysis:", error);
        return;
    }

    const extracted = analysis.extracted_information || {};

    // Safely create text elements
    function createText(tag, text, className = "") {
        const element = document.createElement(tag);
        element.textContent = String(text);

        if (className) {
            element.className = className;
        }

        return element;
    }

    // Display document summary as bullet points
    function displaySummary() {
        const container = document.getElementById("documentSummary");

        if (!container) return;

        container.replaceChildren();

        const summary = analysis.summary;

        if (Array.isArray(summary) && summary.length > 0) {
            const list = document.createElement("ul");
            list.className = "document-points";

            summary.forEach((item) => {
                const li = document.createElement("li");

                li.textContent = typeof item === "object"
                    ? item.description || item.title || JSON.stringify(item)
                    : String(item);

                list.appendChild(li);
            });

            container.appendChild(list);

        } else if (typeof summary === "string" && summary.trim()) {
            container.textContent = summary;
        } else {
            container.textContent =
                "No summary could be generated from this document.";
        }
    }

    // Display contact information with icons
    function displayContactDetails() {
        const container = document.getElementById("contactDetailsList");

        if (!container) return;

        container.replaceChildren();

        const contactFields = [
            {
                label: "Phone Number",
                icon: "📞",
                values: extracted.phone_numbers
            },
            {
                label: "Email Address",
                icon: "✉️",
                values: extracted.emails
            },
            {
                label: "Website",
                icon: "🌐",
                values: extracted.websites
            },
            {
                label: "Address",
                icon: "📍",
                values: extracted.addresses
            }
        ];

        let found = false;

        contactFields.forEach((field) => {
            if (!Array.isArray(field.values)) return;

            field.values.forEach((value) => {
                if (!value) return;

                found = true;

                const card = document.createElement("div");
                card.className = "result-item contact-item";

                card.appendChild(
                    createText("h3", field.icon + " " + field.label)
                );

                card.appendChild(
                    createText("p", value)
                );

                container.appendChild(card);
            });
        });

        if (!found) {
            container.appendChild(
                createText("p", "No contact details were detected.")
            );
        }
    }

    // Display important points from the AI analysis
    function displayImportantInformation() {
        const container = document.getElementById("conditionsList");

        if (!container) return;

        container.replaceChildren();

        const importantPoints = [];

        // Use AI summary as the primary source.
        if (Array.isArray(analysis.summary)) {
            importantPoints.push(...analysis.summary);
        } else if (typeof analysis.summary === "string") {
            importantPoints.push(analysis.summary);
        }

        // Include additional factual points if provided.
        if (Array.isArray(analysis.important_points)) {
            importantPoints.push(...analysis.important_points);
        }

        const uniquePoints = [...new Set(
            importantPoints
                .map((item) => {
                    if (typeof item === "object" && item !== null) {
                        return item.description || item.title || "";
                    }
                    return String(item || "");
                })
                .filter((item) => item.trim())
        )];

        if (uniquePoints.length === 0) {
            container.appendChild(
                createText("p", "No additional information was identified.")
            );
            return;
        }

        const list = document.createElement("ul");
        list.className = "document-points";

        uniquePoints.forEach((point) => {
            list.appendChild(createText("li", point));
        });

        container.appendChild(list);
    }

    // Display all available extracted information
    function displayExtractedInformation() {
        const container = document.getElementById(
            "extractedInformationList"
        );

        if (!container) return;

        container.replaceChildren();

        const fields = [
            ["Names", "👤", extracted.names],
            ["Education", "🎓", extracted.education],
            ["Skills", "💻", extracted.skills],
            ["Experience", "💼", extracted.experience],
            ["Projects", "📂", extracted.projects],
            ["Certifications", "📜", extracted.certifications],
            ["Achievements", "🏆", extracted.achievements],
            ["Dates", "📅", extracted.dates],
            ["Financial Amounts", "💰", extracted.amounts],
            ["Other Details", "📌", extracted.other_details]
        ];

        let found = false;

        fields.forEach(([heading, icon, values]) => {
            if (!Array.isArray(values) || values.length === 0) {
                return;
            }

            found = true;

            const group = document.createElement("div");
            group.className = "result-item";

            group.appendChild(
                createText("h3", icon + " " + heading)
            );

            const list = document.createElement("ul");

            values.forEach((value) => {
                list.appendChild(createText("li", value));
            });

            group.appendChild(list);
            container.appendChild(group);
        });

        if (!found) {
            container.appendChild(
                createText(
                    "p",
                    "Additional structured details were not detected."
                )
            );
        }

        // Show how much document text was analysed.
        if (analysis.analysis_coverage) {
            const coverage = document.createElement("p");

            coverage.className = "coverage-note";

            coverage.textContent =
                "Document sections analysed: " +
                (analysis.analysis_coverage.sections_analyzed || 0) +
                " | Characters processed: " +
                (analysis.analysis_coverage.total_characters || 0);

            container.appendChild(coverage);
        }
    }

    // Display Tamil explanation
    function displayTamilSummary() {
        const container = document.getElementById("tamilSummary");

        if (!container) return;

        container.replaceChildren();

        const tamil = analysis.tamil_summary;

        if (Array.isArray(tamil) && tamil.length > 0) {
            const list = document.createElement("ul");
            list.className = "document-points";

            tamil.forEach((item) => {
                list.appendChild(
                    createText("li", item)
                );
            });

            container.appendChild(list);

        } else if (typeof tamil === "string" && tamil.trim()) {
            container.textContent = tamil;
        } else {
            container.textContent =
                "இந்த ஆவணத்திற்கான தமிழ் விளக்கம் உருவாக்கப்படவில்லை.";
        }
    }

    // Display document type
    const documentType = document.getElementById("documentType");

    if (documentType) {
        documentType.textContent =
            analysis.document_type || "Analysed Document";
    }

    // Display all sections
    displaySummary();
    displayContactDetails();
    displayImportantInformation();
    displayExtractedInformation();
    displayTamilSummary();

    // Display disclaimer
    const disclaimer = document.getElementById("disclaimer");

    if (disclaimer) {
        disclaimer.textContent =
            analysis.disclaimer ||
            "CLARIFY AI extracts and explains information from your document. " +
            "Always verify important details against the original document.";
    }

    console.log("CLARIFY AI Smart Document Reader loaded.");
});
