"""
pdf_extractor.py (v2)
-----------------
Handles extracting text from uploaded PDF financial reports.
Uses pdfplumber, which is good at handling the complex layouts
found in 10-K filings and earnings reports.

v2 change: the default truncation limit is raised from 80k to 200k
characters (bumped again from an initial 150k). The v2 summarizer asks
Claude to dig into multi-year history, segment breakdowns, ratio
analysis, and now a growth-outlook read that leans on cash flow and
R&D/capex disclosures — all of which live deeper in a filing than the
front-page summary — so more of the document needs to survive
truncation for the deeper prompt to have anything to work with.
"""

import pdfplumber


def extract_text_from_pdf(pdf_file) -> str:
    """
    Takes a PDF file and returns all the text content as a single string.

    Args:
        pdf_file: A file-like object (e.g., from Streamlit's file uploader)

    Returns:
        A tuple of (combined_text, total_pages)
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


def truncate_text(text: str, max_chars: int = 200_000) -> str:
    """
    Financial reports can be very long (200+ pages). Claude has a context
    window limit, so we truncate to the most important parts.

    The beginning of a report usually contains the financial statements
    and key summaries, and the notes/segment disclosures/risk factors
    that v2's deeper analysis relies on tend to show up later — so we
    keep a larger slice than v1 and split it more evenly between the
    front and back of the document.

    Args:
        text: The full extracted text
        max_chars: Maximum characters to keep (default 200,000 ≈ ~50k tokens)

    Returns:
        Truncated text that fits within the limit
    """
    if len(text) <= max_chars:
        return text

    # Keep the first portion (financial statements, summary, MD&A)
    # and a larger last portion than v1 (segment notes, risk factors,
    # historical data tables are often further back in the document)
    first_portion = text[: max_chars * 3 // 5]
    last_portion = text[-max_chars * 2 // 5 :]

    return (
        first_portion
        + "\n\n[... middle section omitted for length ...]\n\n"
        + last_portion
    )
