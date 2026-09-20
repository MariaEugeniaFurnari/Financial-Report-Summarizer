"""
summarizer.py (v2)
--------------
Sends extracted financial report text to the Claude API and gets back
a much more detailed structured analysis than v1.

v1 returned a quick snapshot: headline financials, a short summary,
a handful of bullet-point strengths/risks. v2 asks for a genuine
analyst-style deep dive on top of that: financial ratios, a
business/segment breakdown, multi-period trend analysis, a critical
read of management's narrative, and an explicit "red flags" pass —
each with a paragraph or two of reasoning behind it, not just a label.

Updated to go longer and deeper still: the ratio panel now covers
leverage, margins, cash-flow quality, and growth-investment signals
(14 ratios instead of 7), every narrative section asks for more
sentences with specific numbers cited inline, and there's a new
dedicated "growth_outlook" section — catalysts and headwinds for
future growth, rated and synthesized, separate from the general
strengths/risks list.

This is where the "AI" part of the project lives.
"""

import json
import anthropic

# Same model as v1 for consistency. Verify this is still a valid model
# ID before running — Anthropic model names change over time.
MODEL = "claude-sonnet-4-6"

# v2's prompt asks for a lot more prose per section, so it needs a much
# larger output budget than v1's 2000 tokens. Bumped again to 16000 to
# fit the expanded ratio panel and growth-outlook section — if your
# account's model errors saying max_tokens is too high, lower this
# (some models cap output well below this).
MAX_TOKENS = 16000


def summarize_report(text: str, api_key: str) -> dict:
    """
    Sends the report text to Claude and asks it for a detailed financial
    analysis: ratios, historical trend, segment breakdown, and a critical
    read of management's narrative — not just a snapshot of the headline
    numbers.

    Args:
        text: The extracted text from the financial report
        api_key: Your Anthropic API key

    Returns:
        A dictionary containing the structured analysis
    """

    client = anthropic.Anthropic(api_key=api_key)

    prompt = f"""You are a senior equity research analyst writing a long, detailed internal deep-dive note on a company, based on text extracted from one of its financial reports (10-K, 10-Q, or earnings report). The reader of this note wants real depth — specific numbers cited inline, not vague qualitative statements — so write accordingly: every narrative field below should read like analyst prose full of figures, not a list of adjectives.

Go beyond a surface-level summary. Analyze the numbers, cross-check them against what management says, look across every period the document reports (not just the most recent one), and flag anything that looks inconsistent, aggressive, or worth a closer look. Where the document doesn't give you enough to calculate something precisely, make that explicit rather than guessing — never fabricate a number to fill a field.

Return a JSON object with exactly this structure. Use null for any field you genuinely cannot support from the document — do not fabricate numbers or invent segments/periods that aren't in the text.

{{
    "company_name": "The company's name",
    "report_type": "10-K, 10-Q, or Earnings Report",
    "period": "The fiscal period covered (e.g., FY 2024, Q3 2024)",

    "business_overview": "3-5 sentences on what the company actually does, its main lines of business, its competitive position, and the scale of its operations (cite revenue/headcount/market figures if given), based only on what the document says.",

    "summary": "A 7-10 sentence executive summary of financial performance during this period, written for someone who will NOT read the rest of the report — hit every major number (revenue, margins, net income, cash flow, per-share figures) and the most important story behind them, with specific figures cited inline rather than described only in general terms.",

    "key_financials": {{
        "revenue": "Total revenue/sales figure with currency",
        "revenue_growth": "Year-over-year revenue growth as a percentage",
        "net_income": "Net income figure with currency",
        "net_income_growth": "Year-over-year net income growth as a percentage",
        "gross_margin": "Gross margin percentage",
        "operating_margin": "Operating margin percentage",
        "eps": "Earnings per share (diluted)",
        "free_cash_flow": "Free cash flow figure if available"
    }},

    "financial_ratios": {{
        "current_ratio": "Current assets / current liabilities, or null if not calculable",
        "quick_ratio": "(Current assets - inventory) / current liabilities, or null",
        "debt_to_equity": "Total debt / shareholders' equity, or null",
        "revenue_cagr": "Compound annual growth rate of revenue across the periods in historical_data, as a percentage, or null if fewer than 2 periods are available (use annual periods if both annual and quarterly are present; if only quarterly, note that in the notes field)",
        "debt_to_ebitda": "Total debt / EBITDA, or null — a leverage measure relative to cash earnings power",
        "return_on_equity": "Net income / shareholders' equity, as a percentage, or null",
        "return_on_assets": "Net income / total assets, as a percentage, or null",
        "asset_turnover": "Revenue / total assets, or null",
        "interest_coverage": "Operating income / interest expense, or null",
        "net_margin": "Net income / revenue, as a percentage, or null",
        "ebitda_margin": "EBITDA / revenue, as a percentage, or null if EBITDA isn't derivable from the text",
        "cash_conversion": "Free cash flow / net income, as a ratio or percentage — a signal of earnings quality (are reported profits actually turning into cash), or null",
        "capex_to_revenue": "Capital expenditures / revenue, as a percentage — signals how much the company reinvests to support growth, or null",
        "rd_to_revenue": "R&D expense / revenue, as a percentage, if disclosed and relevant to this industry, or null",
        "dividend_payout": "Dividends paid / net income, as a percentage, or null if the company pays no dividend",
        "notes": "2-3 sentences flagging any ratios you could not calculate and why (e.g. balance sheet or cash flow statement not included in extracted text), so the reader knows which numbers are missing rather than assuming null means zero"
    }},

    "historical_data": [
        {{
            "period": "e.g. FY2022, FY2023, FY2024 or Q1 2024, Q2 2024, ...",
            "revenue": 1000000,
            "net_income": 200000,
            "eps": 1.23
        }}
    ],

    "segments": [
        {{
            "name": "Business segment or product line name",
            "revenue": 1000000,
            "operating_income": 200000,
            "pct_of_total_revenue": "e.g. 34%",
            "commentary": "2-3 sentences on how this segment performed, citing specific figures, and why it matters to the overall business"
        }}
    ],

    "trend_analysis": "5-7 sentence analysis of the trajectory across ALL periods found in historical_data, citing specific period-over-period numbers — is growth accelerating or decelerating (with the actual growth rates per period), are margins expanding or compressing (with the actual margin figures), is the revenue/profit mix shifting between segments, how does capital allocation (buybacks, dividends, capex, debt paydown or issuance) compare period over period.",

    "management_discussion_analysis": "5-7 sentences critically assessing management's narrative — does the tone match the numbers, are there hedges or vague language around weak areas, is guidance consistent with the trend shown in the data, anything that reads as spin versus what the figures actually show. Quote or closely paraphrase specific language from the document where it supports your read.",

    "growth_outlook": {{
        "growth_rating": "One of: Strong, Moderate, Weak, or Uncertain — your overall read of the company's forward growth potential based only on evidence in this document",
        "growth_catalysts": [
            "4-6 specific factors supporting future growth, each a full sentence with the reasoning and, where possible, a supporting number — e.g. an accelerating or high-margin segment, rising R&D/capex investment, expanding backlog or bookings, strong guidance relative to trend, market share gains, pricing power"
        ],
        "growth_headwinds": [
            "4-6 specific factors that could limit or threaten future growth, each a full sentence with the reasoning and, where possible, a supporting number — e.g. decelerating growth rates, margin compression, rising competitive pressure, customer or segment concentration, leverage constraints on reinvestment, guidance that undershoots the recent trend"
        ],
        "growth_outlook_summary": "4-6 sentence synthesis of the growth picture: is this a business investing in growth or harvesting cash (cite the capex/R&D trend), is growth broad-based across segments or narrow, and what would need to be true for growth to accelerate or stall from here. Frame this as analysis, not a recommendation."
    }},

    "strengths": [
        "3-5 specific strengths, each written as a full sentence with the reasoning and a supporting figure where possible, not just a label"
    ],

    "risks": [
        "3-5 specific risks or concerns, each written as a full sentence with the reasoning and a supporting figure where possible, not just a label"
    ],

    "red_flags": [
        "0-4 items that go beyond the normal 'risks' disclosure — things like a mismatch between reported earnings and cash flow, one-time items inflating a headline number, unusual changes in reserves or estimates, guidance that seems disconnected from trend, or heavy reliance on non-GAAP metrics. Return an empty list if nothing stands out — do not invent a red flag to fill the field."
    ],

    "guidance": "Any forward-looking guidance or outlook the company provided, with the specific figures/ranges given, or null if not found",

    "analyst_take": "3-4 sentence closing assessment of the overall picture (e.g. improving, stable, deteriorating, and why, citing the numbers that most support that read) — framed as one analyst's read of this document, not as investment advice, and without a buy/sell/hold recommendation."
}}

IMPORTANT:
- Return ONLY valid JSON, no other text before or after.
- Every narrative field (business_overview, summary, trend_analysis, management_discussion_analysis, growth_outlook_summary, analyst_take, and each item in segments/strengths/risks/growth_catalysts/growth_headwinds) should cite specific numbers from the document wherever possible — avoid vague language like "strong performance" without the figure behind it.
- For historical_data, extract every period the document reports (both annual and quarterly if both appear), not just the most recent one. Use raw numbers (no currency symbols) for revenue, net_income, and eps.
- For segments, only include this if the document actually discloses segment-level or product-line-level financials. Return an empty list if it doesn't.
- This analysis is for informational purposes only and is not financial advice — do not phrase analyst_take, strengths, risks, or growth_outlook as a recommendation to buy, sell, or hold, and do not treat growth_rating as a price target or rating in the equity-research-firm sense.
- If the document doesn't appear to be a financial report, return {{"error": "This doesn't appear to be a financial report."}}.

Here is the report text:

{text}"""

    message = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    response_text = message.content[0].text

    # Clean up the response in case Claude wraps it in markdown code blocks
    response_text = response_text.strip()
    if response_text.startswith("```json"):
        response_text = response_text[7:]
    if response_text.startswith("```"):
        response_text = response_text[3:]
    if response_text.endswith("```"):
        response_text = response_text[:-3]
    response_text = response_text.strip()

    try:
        result = json.loads(response_text)
    except json.JSONDecodeError:
        result = {
            "error": "Failed to parse the AI response. The report format may not be supported.",
            "raw_response": response_text
        }

    return result
