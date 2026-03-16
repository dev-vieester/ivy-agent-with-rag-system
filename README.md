# Ivy Assistant

An AI agent built with LangChain and Anthropic Claude that combines
RAG (Retrieval-Augmented Generation) for internal company knowledge
with a suite of tools for web search, CSV analysis, report generation,
email delivery, and reminders.

## Features

- **RAG** — ingest and query internal PDF, DOCX, and CSV files via ChromaDB
- **Web search** — DuckDuckGo search, no API key required
- **CSV analysis** — preview, filter, summarize, and export CSV data
- **Report export** — generate PDF, DOCX, or TXT reports
- **Email** — send emails with optional file attachments via Gmail SMTP
- **Reminders** — schedule one-time or recurring reminders

## Project Structure
```
Ivy_Assistant/
├── agents/
│   ├── retrieval_agent.py     # RAG ingestion and retrieval
│   └── ivy_agent.py           # Main LangChain agent loop
├── rag/
│   ├── embedding_manager.py   # Embedding generation (SentenceTransformer / Gemini)
│   ├── rag_retriever.py       # Query-based vector store retrieval
│   ├── retrieve_document.py   # Document loading (PDF, TXT, CSV)
│   ├── split_documents.py     # Document chunking
│   └── vector_store.py        # ChromaDB vector store manager
├── tools/
│   ├── lc_tools.py            # LangChain @tool wrappers
│   ├── tool_registry.py       # Tool function + schema registry
│   ├── web_search_tool.py     # DuckDuckGo web search
│   ├── csv_analyzer.py        # CSV preview, stats, filter, export
│   ├── send_mail_tool.py      # Gmail SMTP email sender
│   ├── summarize_export_tool.py # PDF/DOCX/TXT report export
│   └── reminder_tool.py       # APScheduler-based reminders
├── data/
│   ├── pdf_files/             # Company PDF documents
│   ├── doc_files/             # Company TXT documents
│   └── csv_files/             # Company CSV files
├── main.py                    # Entry point
├── ingest.py                  # Run once to populate vector store
├── requirements.txt
└── .env.example
```

## Setup

1. Clone the repo and install dependencies:
```bash
   pip install -r requirements.txt
```

2. Copy `.env.example` to `.env` and fill in your keys:
```bash
   cp .env.example .env
```

3. Add your company files to `data/pdf_files/`, `data/doc_files/`, `data/csv_files/`

4. Ingest documents into the vector store:
```bash
   python ingest.py
```

5. Run the agent:
```bash
   python main.py
```

## Environment Variables

| Variable | Description |
|---|---|
| `ANTHROPIC_API_KEY` | Your Anthropic API key |
| `GMAIL_SENDER` | Gmail address to send emails from |
| `GMAIL_APP_PASSWORD` | Gmail app password (not your login password) |
| `GOOGLE_API_KEY` | Optional — only if using Gemini embeddings |
