# Automated Financial Report Summarizer

An AI-powered tool that extracts key financial data from earnings reports and 10-K filings, then generates clear, plain-English summaries — so you can spend less time reading 200-page documents and more time analyzing.

## What It Does

1. **Upload** a PDF of a financial report (10-K, 10-Q, earnings report)
2. **Extract** text automatically from the document
3. **Summarize** key financials using AI (revenue, net income, margins, guidance, risks)
4. **Display** results in a clean, interactive dashboard

## Tech Stack

- **Python 3.10+**
- **Streamlit** — simple web interface
- **pdfplumber** — PDF text extraction
- **Anthropic API (Claude)** — AI-powered summarization
- **Plotly** — interactive charts

## Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/financial-report-summarizer.git
cd financial-report-summarizer
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv

# On Mac/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Get your Anthropic API key

- Go to https://console.anthropic.com/
- Sign up or log in
- Create an API key
- Copy it somewhere safe

### 5. Set up your API key

Create a file called `.env` in the project folder:

```
ANTHROPIC_API_KEY=your-api-key-here
```

### 6. Run the app

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`.

## Project Structure

```
financial-report-summarizer/
├── app.py                 # Main Streamlit app (the web interface)
├── pdf_extractor.py       # Handles reading text from PDF files
├── summarizer.py          # Sends text to Claude API for analysis
├── requirements.txt       # Python packages needed
├── .env                   # Your API key (don't commit this!)
├── .gitignore             # Tells Git what to ignore
└── README.md              # This file
```

## How It Works (For Interviews)

This project demonstrates:

- **PDF parsing** — extracting structured text from complex financial documents
- **AI prompt engineering** — crafting prompts that reliably extract specific financial metrics
- **Data presentation** — turning raw AI output into a clean, readable dashboard
- **Error handling** — gracefully managing edge cases (scanned PDFs, missing data, API failures)
- **Practical AI application** — using AI to automate a real financial analyst workflow

## Future Improvements

- Support for comparing multiple quarters side by side
- Export summaries to Excel or PDF
- Add sentiment analysis on management discussion sections
- Support for batch processing multiple filings
- Pull filings directly from SEC EDGAR

## License

MIT
