"""
app.py (v2)
-------
The v2 Streamlit application: a deeper, analyst-style report on top of
the same PDF-upload flow as v1. Run with: streamlit run app.py

What's new vs v1:
    - Business overview + a longer executive summary
    - Expanded financial ratio panel: liquidity, leverage, returns,
      margins, cash-flow quality, and growth-investment signals
      (14 ratios instead of 7)
    - Multi-period historical trend chart (annual AND quarterly, not
      just the quarters in one filing) with a "view as table" toggle
    - Segment / business-line breakdown, when the filing discloses one
    - A trend-analysis narrative and a critical read of management's
      discussion, not just a metrics grid
    - A dedicated Growth Outlook section: a growth rating, revenue
      CAGR, and specific growth catalysts vs. headwinds — separate
      from the general strengths/risks list
    - An explicit "red flags" pass, separate from the normal risks list
    - An analyst's-take closing line, with a clear non-advice disclaimer
"""

import streamlit as st
import plotly.graph_objects as go
from dotenv import load_dotenv
import os

from pdf_extractor import extract_text_from_pdf, truncate_text
from summarizer import summarize_report

load_dotenv()

# --- Page Configuration ---
st.set_page_config(
    page_title="Financial Report Summarizer — Deep Dive",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Financial Report Summarizer — Deep Dive (v2)")
st.markdown(
    "Upload a 10-K, 10-Q, or earnings report PDF and get an analyst-style "
    "deep dive: ratios, multi-period trends, segment breakdown, and a "
    "critical read of management's narrative — not just a snapshot."
)
st.divider()


# --- Sidebar: API Key Setup ---
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
    st.markdown("3. Review the deep-dive analysis")

    st.divider()
    st.caption(
        "v2 sends more of the document per report and asks for a longer "
        "response, so each analysis costs more and takes longer than v1."
    )


# --- Main Section: File Upload ---
uploaded_file = st.file_uploader(
    "Upload a financial report (PDF)",
    type=["pdf"],
    help="Works best with 10-K, 10-Q, and quarterly earnings reports"
)

if uploaded_file and api_key:

    if st.button("🔍 Analyze Report", type="primary", use_container_width=True):

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

            st.write("✂️ Preparing text for analysis...")
            truncated_text = truncate_text(text)

            st.write("🤖 AI is building a deep-dive analysis (this takes longer than a quick summary)...")
            result = summarize_report(truncated_text, api_key)

            status.update(label="Analysis complete!", state="complete")

        if "error" in result:
            st.error(result["error"])
            st.stop()

        st.session_state["result"] = result

    if "result" in st.session_state:
        result = st.session_state["result"]

        # --- Company Header ---
        st.header(result.get("company_name", "Company Report"))

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Report Type", result.get("report_type", "N/A"))
        with col2:
            st.metric("Period", result.get("period", "N/A"))

        business_overview = result.get("business_overview")
        if business_overview:
            st.markdown(f"*{business_overview}*")

        st.divider()

        # --- Executive Summary ---
        st.subheader("📋 Executive Summary")
        st.write(result.get("summary", "No summary available."))

        st.divider()

        # --- Key Financial Metrics ---
        st.subheader("💰 Key Financials")

        financials = result.get("key_financials", {})

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

        # --- Financial Ratios (expanded: liquidity, leverage, returns, margins, cash-flow quality, growth investment) ---
        st.subheader("📐 Financial Ratios")

        ratios = result.get("financial_ratios", {})

        st.caption("Liquidity & leverage")
        ratio_cols = st.columns(4)
        with ratio_cols[0]:
            st.metric("Current Ratio", ratios.get("current_ratio") or "N/A")
        with ratio_cols[1]:
            st.metric("Quick Ratio", ratios.get("quick_ratio") or "N/A")
        with ratio_cols[2]:
            st.metric("Debt / Equity", ratios.get("debt_to_equity") or "N/A")
        with ratio_cols[3]:
            st.metric("Debt / EBITDA", ratios.get("debt_to_ebitda") or "N/A")

        st.caption("Returns & efficiency")
        ratio_cols2 = st.columns(4)
        with ratio_cols2[0]:
            st.metric("Return on Equity", ratios.get("return_on_equity") or "N/A")
        with ratio_cols2[1]:
            st.metric("Return on Assets", ratios.get("return_on_assets") or "N/A")
        with ratio_cols2[2]:
            st.metric("Asset Turnover", ratios.get("asset_turnover") or "N/A")
        with ratio_cols2[3]:
            st.metric("Interest Coverage", ratios.get("interest_coverage") or "N/A")

        st.caption("Margins & cash-flow quality")
        ratio_cols3 = st.columns(4)
        with ratio_cols3[0]:
            st.metric("Net Margin", ratios.get("net_margin") or "N/A")
        with ratio_cols3[1]:
            st.metric("EBITDA Margin", ratios.get("ebitda_margin") or "N/A")
        with ratio_cols3[2]:
            st.metric("Cash Conversion", ratios.get("cash_conversion") or "N/A")
        with ratio_cols3[3]:
            st.metric("Capex / Revenue", ratios.get("capex_to_revenue") or "N/A")

        st.caption("Growth investment & shareholder returns")
        ratio_cols4 = st.columns(2)
        with ratio_cols4[0]:
            st.metric("R&D / Revenue", ratios.get("rd_to_revenue") or "N/A")
        with ratio_cols4[1]:
            st.metric("Dividend Payout", ratios.get("dividend_payout") or "N/A")

        ratio_notes = ratios.get("notes")
        if ratio_notes:
            st.caption(f"ℹ️ {ratio_notes}")

        st.divider()

        # --- Historical Trend (expanded in v2: annual + quarterly, not just quarters in this filing) ---
        historical_data = result.get("historical_data", [])

        if historical_data and len(historical_data) > 1:
            st.subheader("📈 Historical Trend")

            periods = [p.get("period", "") for p in historical_data]
            revenues = [p.get("revenue", 0) or 0 for p in historical_data]
            net_incomes = [p.get("net_income", 0) or 0 for p in historical_data]

            # Single categorical pair, fixed order, validated for colorblind
            # separation (ΔE 31.3 deutan / 37.1 normal-vision) — same colors
            # v1 used, kept for continuity across versions.
            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=periods,
                y=revenues,
                name="Revenue",
                mode="lines+markers",
                line=dict(color="#4F46E5", width=2),
                marker=dict(size=8)
            ))

            fig.add_trace(go.Scatter(
                x=periods,
                y=net_incomes,
                name="Net Income",
                mode="lines+markers",
                line=dict(color="#10B981", width=2),
                marker=dict(size=8)
            ))

            fig.update_layout(
                xaxis_title="Period",
                yaxis_title="Amount",
                legend=dict(orientation="h", yanchor="bottom", y=1.02),
                margin=dict(t=40, b=40),
                height=400
            )

            st.plotly_chart(fig, use_container_width=True)

            # Table view alongside the chart — required relief for the
            # green series, which falls below 3:1 contrast against a
            # light surface on its own.
            with st.expander("View as table"):
                st.dataframe(
                    [
                        {
                            "Period": p.get("period", ""),
                            "Revenue": p.get("revenue"),
                            "Net Income": p.get("net_income"),
                            "EPS": p.get("eps"),
                        }
                        for p in historical_data
                    ],
                    use_container_width=True,
                    hide_index=True
                )

            st.divider()

        trend_analysis = result.get("trend_analysis")
        if trend_analysis:
            st.subheader("🧭 Trend Analysis")
            st.write(trend_analysis)
            st.divider()

        # --- Segment Breakdown (new in v2) ---
        segments = result.get("segments", [])

        if segments:
            st.subheader("🧩 Segment Breakdown")

            seg_names = [s.get("name", "") for s in segments]
            seg_revenues = [s.get("revenue", 0) or 0 for s in segments]

            seg_fig = go.Figure()
            seg_fig.add_trace(go.Bar(
                x=seg_revenues,
                y=seg_names,
                orientation="h",
                marker_color="#4F46E5",
                text=[s.get("pct_of_total_revenue", "") for s in segments],
                textposition="outside"
            ))
            seg_fig.update_layout(
                xaxis_title="Revenue",
                margin=dict(t=20, b=40),
                height=max(250, 60 * len(segments))
            )
            st.plotly_chart(seg_fig, use_container_width=True)

            for s in segments:
                commentary = s.get("commentary")
                if commentary:
                    st.markdown(f"**{s.get('name', 'Segment')}** — {commentary}")

            st.divider()

        # --- Management Discussion Analysis (new in v2) ---
        mdna = result.get("management_discussion_analysis")
        if mdna:
            st.subheader("🗣️ Reading Management's Narrative")
            st.write(mdna)
            st.divider()

        # --- Growth Outlook: catalysts and headwinds for future growth, separate from general strengths/risks ---
        growth_outlook = result.get("growth_outlook", {})

        if growth_outlook:
            st.subheader("🌱 Growth Outlook")

            go_col1, go_col2 = st.columns(2)
            with go_col1:
                st.metric("Growth Rating", growth_outlook.get("growth_rating") or "N/A")
            with go_col2:
                st.metric("Revenue CAGR", ratios.get("revenue_cagr") or "N/A")

            outlook_summary = growth_outlook.get("growth_outlook_summary")
            if outlook_summary:
                st.write(outlook_summary)

            catalyst_col, headwind_col = st.columns(2)

            with catalyst_col:
                st.markdown("**📈 Growth Catalysts**")
                catalysts = growth_outlook.get("growth_catalysts", [])
                if catalysts:
                    for c in catalysts:
                        st.markdown(f"- {c}")
                else:
                    st.write("No specific growth catalysts identified.")

            with headwind_col:
                st.markdown("**📉 Growth Headwinds**")
                headwinds = growth_outlook.get("growth_headwinds", [])
                if headwinds:
                    for h in headwinds:
                        st.markdown(f"- {h}")
                else:
                    st.write("No specific growth headwinds identified.")

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

        # --- Red Flags (new in v2) ---
        red_flags = result.get("red_flags", [])
        if red_flags:
            st.subheader("🚩 Red Flags")
            for flag in red_flags:
                st.warning(flag)
            st.divider()

        # --- Forward Guidance ---
        guidance = result.get("guidance")
        if guidance:
            st.subheader("🔮 Forward Guidance")
            st.write(guidance)
            st.divider()

        # --- Analyst's Take (new in v2) ---
        analyst_take = result.get("analyst_take")
        if analyst_take:
            st.subheader("🧑‍💼 Analyst's Take")
            st.info(analyst_take)

        st.caption(
            "This analysis is AI-generated from the uploaded document for "
            "informational purposes only. It is not financial advice and "
            "should not be the sole basis for an investment decision — "
            "verify anything important against the original filing."
        )

elif not api_key:
    st.info("👈 Please add your Anthropic API key in the sidebar to get started.")
elif not uploaded_file:
    st.info("👆 Upload a financial report PDF to get started.")
