
document.addEventListener("DOMContentLoaded", () => {

    const analysisForm = document.getElementById("analysisForm");
    const documentFile = document.getElementById("documentFile");
    const documentText = document.getElementById("documentText");
    const language = document.getElementById("language");
    const analyseButton = document.getElementById("analyseButton");
    const statusMessage = document.getElementById("statusMessage");
    const fileName = document.getElementById("fileName");
    const uploadArea = document.getElementById("uploadArea");

    // Stop if this page does not contain the upload form.
    if (!analysisForm) return;

    // Display selected PDF filename.
    documentFile.addEventListener("change", () => {

        const file = documentFile.files[0];

        if (!file) {
            fileName.textContent = "";
            return;
        }

        if (!file.name.toLowerCase().endsWith(".pdf")) {
            showMessage("Please select a PDF file.", "error");
            documentFile.value = "";
            fileName.textContent = "";
            return;
        }

        if (file.size > 10 * 1024 * 1024) {
            showMessage("File size must be below 10 MB.", "error");
            documentFile.value = "";
            fileName.textContent = "";
            return;
        }

        fileName.textContent = "✓ Selected: " + file.name;
        showMessage("", "");
    });

    // Drag and drop functionality.
    if (uploadArea) {

        uploadArea.addEventListener("dragover", (event) => {
            event.preventDefault();
            uploadArea.classList.add("dragover");
        });

        uploadArea.addEventListener("dragleave", () => {
            uploadArea.classList.remove("dragover");
        });

        uploadArea.addEventListener("drop", (event) => {
            event.preventDefault();
            uploadArea.classList.remove("dragover");

            const file = event.dataTransfer.files[0];

            if (!file) return;

            if (!file.name.toLowerCase().endsWith(".pdf")) {
                showMessage("Only PDF files are supported.", "error");
                return;
            }

            if (file.size > 10 * 1024 * 1024) {
                showMessage("File size must be below 10 MB.", "error");
                return;
            }

            const transfer = new DataTransfer();
            transfer.items.add(file);
            documentFile.files = transfer.files;

            fileName.textContent = "✓ Selected: " + file.name;
            showMessage("", "");
        });
    }

    // Submit document for AI analysis.
    analysisForm.addEventListener("submit", async (event) => {

        event.preventDefault();

        const selectedFile = documentFile.files[0];
        const pastedText = documentText.value.trim();
        const selectedLanguage = language.value;

        // Validate input.
        if (!selectedFile && !pastedText) {
            showMessage("Please upload a PDF or paste document text.", "error");
            return;
        }

        if (selectedFile && pastedText) {
            showMessage("Please upload a PDF OR paste text, not both.", "error");
            return;
        }

        if (pastedText && pastedText.length < 50) {
            showMessage("Please enter at least 50 characters of document text.", "error");
            return;
        }

        if (selectedFile && selectedFile.size > 10 * 1024 * 1024) {
            showMessage("File size must be below 10 MB.", "error");
            return;
        }

        // Prepare data for Flask backend.
        const formData = new FormData();

        if (selectedFile) {
            formData.append("file", selectedFile);
        } else {
            formData.append("text", pastedText);
        }

        formData.append("language", selectedLanguage);

        // Loading state.
        analyseButton.disabled = true;
        analyseButton.textContent = "Analysing Document...";
        showMessage(
            "CLARIFY AI is reading your document and identifying important conditions. Please wait...",
            "loading"
        );

        try {

            const response = await fetch("/api/analyze", {
                method: "POST",
                body: formData
            });

            const result = await response.json();

            if (!response.ok || result.status !== "success") {
                throw new Error(
                    result.message || result.error || "Document analysis failed."
                );
            }

            // Save the analysis for the results page.
            const analysisData = result.analysis || result.data || result;

            sessionStorage.setItem(
                "clarifyAnalysis",
                JSON.stringify(analysisData)
            );

            sessionStorage.setItem(
                "clarifyLanguage",
                selectedLanguage
            );

            showMessage("Analysis completed! Opening your report...", "success");

            // Open results page.
            window.location.href = "/result";

        } catch (error) {

            console.error("CLARIFY AI Error:", error);

            showMessage(
                error.message || "Something went wrong. Please try again.",
                "error"
            );

            analyseButton.disabled = false;
            analyseButton.textContent = "Analyse My Document →";
        }

    });

    // Display status messages.
    function showMessage(message, type) {

        if (!statusMessage) return;

        statusMessage.textContent = message;
        statusMessage.className = "status-message";

        if (type) {
            statusMessage.classList.add(type);
        }
    }

});
