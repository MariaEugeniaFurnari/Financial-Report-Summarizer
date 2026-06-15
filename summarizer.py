"""
summarizer.py
--------------
Sends extracted financial report text to the Claude API
and gets back a structured summary of key financial metrics.

This is where the "AI" part of the project lives.
"""

import json
import anthropic


def summarize_report(text: str, api_key: str) -> dict:
    """
    Sends the report text to Claude and asks it to extract key financial
    data and generate a summary.

    Args:
        text: The extracted text from the financial report
        api_key: Your Anthropic API key

    Returns:
        A dictionary containing the structured summary
    """

    # Initialize the Anthropic client
    client = anthropic.Anthropic(api_key=api_key)

    # This prompt is carefully designed to get consistent, structured output.
    # In interviews, you can talk about how you iterated on this prompt
    # to get reliable results across different report formats.
    prompt = f"""You are a senior financial analyst. I'm giving you text extracted from a financial report (10-K, 10-Q, or earnings report). 

Analyze it and return a JSON object with the following structure. Use null for any field you cannot find in the document.

{{
    "company_name": "The company's name",
    "report_type": "10-K, 10-Q, or Earnings Report",
    "period": "The fiscal period covered (e.g., FY 2024, Q3 2024)",
    
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
    
    "quarterly_data": [
        {{
            "quarter": "Q1 2024",
            "revenue": 1000000,
            "net_income": 200000
        }}
    ],
    
    "summary": "A 3-4 sentence executive summary of the company's financial performance during this period. Highlight the most important trends.",
    
    "strengths": ["List 3-4 key strengths or positive highlights"],
    
    "risks": ["List 3-4 key risks or concerns mentioned in the report"],
    
    "guidance": "Any forward-looking guidance or outlook the company provided, or null if not found"
}}

IMPORTANT: 
- Return ONLY valid JSON, no other text before or after.
- For quarterly_data, extract as many quarters as you can find. Use raw numbers (no currency symbols) for the revenue and net_income fields.
- If the document doesn't appear to be a financial report, return {{"error": "This doesn't appear to be a financial report."}}.

Here is the report text:

{text}"""

    # Call the Claude API
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    # Extract the response text
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

    # Parse the JSON response
    try:
        result = json.loads(response_text)
    except json.JSONDecodeError:
        result = {
            "error": "Failed to parse the AI response. The report format may not be supported.",
            "raw_response": response_text
        }

    return result
