
import os
import uuid
from pathlib import Path

from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

from backend.document_processor import extract_document_text
from backend.ai_analyzer import analyze_document
from backend.risk_detector import add_risk_overview

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"
UPLOAD_FOLDER = BASE_DIR / "uploads"

UPLOAD_FOLDER.mkdir(exist_ok=True)

app = Flask(__name__)

app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

ALLOWED_EXTENSIONS = {"pdf"}


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


@app.route("/")
def home():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/dashboard")
def dashboard():
    return send_from_directory(FRONTEND_DIR, "dashboard.html")


@app.route("/result")
def result():
    return send_from_directory(FRONTEND_DIR, "result.html")


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "success",
        "message": "CLARIFY AI backend is running!"
    })


@app.route("/api/analyze", methods=["POST"])
def analyze():
    saved_path = None

    try:
        document_text = ""
        document_name = "Pasted Text"

        if "file" in request.files:
            file = request.files["file"]

            if file and file.filename:
                if not allowed_file(file.filename):
                    return jsonify({
                        "status": "error",
                        "message": "Only PDF files are supported."
                    }), 400

                safe_name = secure_filename(file.filename)
                unique_name = f"{uuid.uuid4().hex}_{safe_name}"
                saved_path = UPLOAD_FOLDER / unique_name

                file.save(saved_path)

                document_text = extract_document_text(saved_path)
                document_name = safe_name

        else:
            document_text = request.form.get("text", "").strip()

        if not document_text:
            return jsonify({
                "status": "error",
                "message": "Please upload a PDF or paste document text."
            }), 400

        if len(document_text) < 50:
            return jsonify({
                "status": "error",
                "message": "Please provide at least 50 characters of document text."
            }), 400

        language = request.form.get("language", "English")

        # Ollama local AI analysis
        analysis = analyze_document(document_text, language)

        # Calculate risk overview
        analysis = add_risk_overview(analysis)

        return jsonify({
            "status": "success",
            "document_name": document_name,
            "analysis": analysis
        })

    except ValueError as error:
        return jsonify({
            "status": "error",
            "message": str(error)
        }), 400

    except Exception as error:
        app.logger.exception("Document analysis failed")

        return jsonify({
            "status": "error",
            "message": f"Document analysis failed: {str(error)}"
        }), 500

    finally:
        if saved_path and saved_path.exists():
            try:
                saved_path.unlink()
            except OSError:
                app.logger.warning(
                    "Could not delete temporary uploaded file."
                )


@app.route("/css/<path:filename>")
def css_files(filename):
    return send_from_directory(FRONTEND_DIR / "css", filename)


@app.route("/js/<path:filename>")
def js_files(filename):
    return send_from_directory(FRONTEND_DIR / "js", filename)


@app.errorhandler(413)
def file_too_large(error):
    return jsonify({
        "status": "error",
        "message": "File is too large. Maximum allowed size is 10 MB."
    }), 413


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
