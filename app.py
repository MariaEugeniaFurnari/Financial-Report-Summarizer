"""
app.py
-------
The main Streamlit application. This is what you run to start the tool.
It provides the web interface where users can upload PDFs and see results.

Run with: streamlit run app.py
"""

import streamlit as st
import plotly.graph_objects as go
from dotenv import load_dotenv
import os

from pdf_extractor import extract_text_from_pdf, truncate_text
from summarizer import summarize_report

# Load environment variables from .env file
load_dotenv()

# --- Page Configuration ---
st.set_page_config(
    page_title="Financial Report Summarizer",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Financial Report Summarizer")
st.markdown("Upload a 10-K, 10-Q, or earnings report PDF and get an AI-powered summary of the key financials.")
st.divider()


# --- Sidebar: API Key Setup ---
# We check for the API key in this order:
# 1. Environment variable (from .env file — recommended)
# 2. User input in the sidebar (for quick testing)
with st.sidebar:
    st.header("⚙️ Settings")

    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        api_key = st.text_input(
            "Anthropic API Key",
            type="password",
            help="Get your key at console.anthropic.com"
        )

    if api_key:
        st.success("API key loaded")
    else:
        st.warning("Please add your API key to the .env file or enter it above.")

    st.divider()
    st.markdown("**How to use:**")
    st.markdown("1. Upload a financial report PDF")
    st.markdown("2. Click 'Analyze Report'")
    st.markdown("3. Review the AI-generated summary")


# --- Main Section: File Upload ---
uploaded_file = st.file_uploader(
    "Upload a financial report (PDF)",
    type=["pdf"],
    help="Works best with 10-K, 10-Q, and quarterly earnings reports"
)

if uploaded_file and api_key:

    # Show a button to start the analysis
    if st.button("🔍 Analyze Report", type="primary", use_container_width=True):

        # --- Step 1: Extract text from the PDF ---
        with st.status("Analyzing your report...", expanded=True) as status:

            st.write("📄 Extracting text from PDF...")
            text, total_pages = extract_text_from_pdf(uploaded_file)

            if not text.strip():
                st.error(
                    "Could not extract text from this PDF. "
                    "It might be a scanned document. "
                    "Try a text-based PDF instead."
                )
                st.stop()

            st.write(f"✅ Extracted text from {total_pages} pages")

            # --- Step 2: Truncate if needed ---
            st.write("✂️ Preparing text for analysis...")
            truncated_text = truncate_text(text)

            # --- Step 3: Send to Claude for summarization ---
            st.write("🤖 AI is analyzing the report...")
            result = summarize_report(truncated_text, api_key)

            status.update(label="Analysis complete!", state="complete")

        # --- Step 4: Display the results ---

        # Check for errors
        if "error" in result:
            st.error(result["error"])
            st.stop()

        # Store result in session state so it persists
        st.session_state["result"] = result

    # Display results if we have them
    if "result" in st.session_state:
        result = st.session_state["result"]

        # --- Company Header ---
        st.header(result.get("company_name", "Company Report"))

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Report Type", result.get("report_type", "N/A"))
        with col2:
            st.metric("Period", result.get("period", "N/A"))

        st.divider()

        # --- Executive Summary ---
        st.subheader("📋 Executive Summary")
        st.write(result.get("summary", "No summary available."))

        st.divider()

        # --- Key Financial Metrics ---
        st.subheader("💰 Key Financials")

        financials = result.get("key_financials", {})

        # Display metrics in a clean grid
        row1_cols = st.columns(4)

        with row1_cols[0]:
            st.metric("Revenue", financials.get("revenue", "N/A"))

        with row1_cols[1]:
            st.metric("Revenue Growth", financials.get("revenue_growth", "N/A"))

        with row1_cols[2]:
            st.metric("Net Income", financials.get("net_income", "N/A"))

        with row1_cols[3]:
            st.metric("Net Income Growth", financials.get("net_income_growth", "N/A"))

        row2_cols = st.columns(4)

        with row2_cols[0]:
            st.metric("Gross Margin", financials.get("gross_margin", "N/A"))

        with row2_cols[1]:
            st.metric("Operating Margin", financials.get("operating_margin", "N/A"))

        with row2_cols[2]:
            st.metric("EPS (Diluted)", financials.get("eps", "N/A"))

        with row2_cols[3]:
            st.metric("Free Cash Flow", financials.get("free_cash_flow", "N/A"))

        st.divider()

        # --- Quarterly Revenue Chart ---
        quarterly_data = result.get("quarterly_data", [])

        if quarterly_data and len(quarterly_data) > 1:
            st.subheader("📈 Quarterly Trends")

            quarters = [q.get("quarter", "") for q in quarterly_data]
            revenues = [q.get("revenue", 0) or 0 for q in quarterly_data]
            net_incomes = [q.get("net_income", 0) or 0 for q in quarterly_data]

            fig = go.Figure()

            fig.add_trace(go.Bar(
                x=quarters,
                y=revenues,
                name="Revenue",
                marker_color="#4F46E5"
            ))

            fig.add_trace(go.Bar(
                x=quarters,
                y=net_incomes,
                name="Net Income",
                marker_color="#10B981"
            ))

            fig.update_layout(
                barmode="group",
                xaxis_title="Quarter",
                yaxis_title="Amount",
                legend=dict(orientation="h", yanchor="bottom", y=1.02),
                margin=dict(t=40, b=40),
                height=400
            )

            st.plotly_chart(fig, use_container_width=True)

            st.divider()

        # --- Strengths & Risks side by side ---
        st.subheader("⚖️ Strengths & Risks")

        str_col, risk_col = st.columns(2)

        with str_col:
            st.markdown("**✅ Strengths**")
            strengths = result.get("strengths", [])
            if strengths:
                for s in strengths:
                    st.markdown(f"- {s}")
            else:
                st.write("No specific strengths identified.")

        with risk_col:
            st.markdown("**⚠️ Risks**")
            risks = result.get("risks", [])
            if risks:
                for r in risks:
                    st.markdown(f"- {r}")
            else:
                st.write("No specific risks identified.")

        st.divider()

        # --- Forward Guidance ---
        guidance = result.get("guidance")
        if guidance:
            st.subheader("🔮 Forward Guidance")
            st.write(guidance)

elif not api_key:
    st.info("👈 Please add your Anthropic API key in the sidebar to get started.")
elif not uploaded_file:
    st.info("👆 Upload a financial report PDF to get started.")
