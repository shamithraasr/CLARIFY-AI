import os
import shutil
from pathlib import Path

# Configure Tesseract for Windows
TESSERACT_DIR = Path(r"C:\Program Files\Tesseract-OCR")
TESSERACT_EXE = TESSERACT_DIR / "tesseract.exe"
TESSDATA_DIR = TESSERACT_DIR / "tessdata"

if TESSERACT_EXE.exists():
    os.environ["PATH"] = (
        str(TESSERACT_DIR) + os.pathsep + os.environ.get("PATH", "")
    )

if TESSDATA_DIR.exists():
    os.environ["TESSDATA_PREFIX"] = str(TESSDATA_DIR)

import pymupdf


def extract_text_from_pdf(file_path):
    """Extract PDF text and OCR scanned pages in English and Tamil."""

    document = None

    try:
        if shutil.which("tesseract") is None:
            raise ValueError(
                "Tesseract OCR was not found. Please check its installation."
            )

        document = pymupdf.open(file_path)

        if document.is_encrypted:
            if not document.authenticate(""):
                raise ValueError(
                    "This PDF is password-protected. "
                    "Please upload an unlocked PDF."
                )

        if len(document) == 0:
            raise ValueError("The PDF contains no pages.")

        extracted_pages = []
        unreadable_pages = []
        ocr_pages = []
        page_errors = []

        total_pages = len(document)

        for page_index, page in enumerate(document):
            page_number = page_index + 1

            try:
                page_text = page.get_text("text").strip()
                image_count = len(page.get_images(full=True))

                # OCR pages containing images or pages without readable text.
                if image_count > 0 or not page_text:
                    try:
                        ocr_text_page = page.get_textpage_ocr(
                            language="eng+tam",
                            dpi=300,
                            full=not bool(page_text)
                        )

                        ocr_text = page.get_text(
                            "text",
                            textpage=ocr_text_page
                        ).strip()

                        if ocr_text:
                            page_text = ocr_text
                            ocr_pages.append(page_number)

                    except Exception as ocr_error:
                        page_errors.append(
                            f"Page {page_number}: OCR failed - {ocr_error}"
                        )

                if page_text:
                    extracted_pages.append(
                        f"\n========== PAGE {page_number} ==========\n"
                        f"{page_text}"
                    )
                else:
                    unreadable_pages.append(page_number)
                    extracted_pages.append(
                        f"\n========== PAGE {page_number} ==========\n"
                        "[EXTRACTION WARNING: No readable text was found. "
                        "This page has not been verified.]"
                    )

            except Exception as page_error:
                unreadable_pages.append(page_number)
                page_errors.append(
                    f"Page {page_number}: Extraction failed - {page_error}"
                )
                extracted_pages.append(
                    f"\n========== PAGE {page_number} ==========\n"
                    "[EXTRACTION WARNING: Page extraction failed.]"
                )

        report = [
            "========== PDF EXTRACTION REPORT ==========",
            f"Total PDF pages: {total_pages}",
            f"Pages processed with OCR: {ocr_pages or 'None'}",
            f"Pages with extraction warnings: "
            f"{unreadable_pages or 'None'}"
        ]

        if page_errors:
            report.append("Page processing errors:")
            report.extend(page_errors)

        if unreadable_pages:
            report.append(
                "IMPORTANT: Some pages could not be read. "
                "The analysis may be incomplete."
            )
        else:
            report.append(
                "All pages produced readable text. "
                "This does not guarantee perfect extraction."
            )

        return "\n".join(report) + "\n" + "\n".join(extracted_pages)

    except Exception as error:
        if isinstance(error, ValueError):
            raise
        raise ValueError(f"PDF extraction failed: {error}")

    finally:
        if document is not None:
            document.close()


def extract_document_text(file_path):
    """Validate the uploaded PDF and extract its contents."""

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError("Uploaded document not found.")

    if path.suffix.lower() != ".pdf":
        raise ValueError("Only PDF documents are supported currently.")

    if path.stat().st_size == 0:
        raise ValueError("The uploaded PDF is empty.")

    return extract_text_from_pdf(path)
