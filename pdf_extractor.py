"""
pdf_extractor.py
-----------------
Handles extracting text from uploaded PDF financial reports.
Uses pdfplumber, which is good at handling the complex layouts
found in 10-K filings and earnings reports.
"""

import pdfplumber


def extract_text_from_pdf(pdf_file) -> str:
    """
    Takes a PDF file and returns all the text content as a single string.

    Args:
        pdf_file: A file-like object (e.g., from Streamlit's file uploader)

    Returns:
        A string containing all extracted text from the PDF
    """
    all_text = []

    with pdfplumber.open(pdf_file) as pdf:
        total_pages = len(pdf.pages)

        for page in pdf.pages:
            page_text = page.extract_text()

            # Some pages might be images or blank — skip those
            if page_text:
                all_text.append(page_text)

    combined_text = "\n\n".join(all_text)

    return combined_text, total_pages


def truncate_text(text: str, max_chars: int = 80000) -> str:
    """
    Financial reports can be very long (200+ pages). Claude has a context
    window limit, so we truncate to the most important parts.

    The beginning of a report usually contains the financial statements
    and key summaries, so we prioritize that content.

    Args:
        text: The full extracted text
        max_chars: Maximum characters to keep (default 80,000 ≈ ~20k tokens)

    Returns:
        Truncated text that fits within the limit
    """
    if len(text) <= max_chars:
        return text

    # Keep the first portion (financial statements, summary)
    # and the last portion (notes, risk factors often at the end)
    first_portion = text[: max_chars * 3 // 4]
    last_portion = text[-max_chars // 4 :]

    return (
        first_portion
        + "\n\n[... middle section omitted for length ...]\n\n"
        + last_portion
    )
