from langchain_core.tools import tool
from agents.retrieval_agent import RetrievalAgent

from tools.web_search_tool import web_search as _web_search
from tools.send_mail_tool import send_email as _send_email
from tools.summarize_export_tool import summarize_and_export as _summarize_and_export
from tools.csv_analyzer import (
    csv_preview as _csv_preview,
    csv_summary_stats as _csv_summary_stats,
    csv_filter as _csv_filter,
    csv_export_analysis as _csv_export_analysis,
)
from tools.reminder_tool import (
    add_reminder as _add_reminder,
    list_reminders as _list_reminders,
    cancel_reminder as _cancel_reminder,
)

# ── RAG tool ──────────────────────────────────────────────────────────────────

_retrieval_agent = RetrievalAgent(
    embedding_model="all-MiniLM-L6-v2",
    embedding_provider="sentence_transformer",
)

@tool
def search_company_docs(query: str, top_k: int = 5) -> str:
    """
    Search internal company documents, policies, reports, employee data,
    and financial records stored in the company knowledge base.
    Use this for any question about internal company information.
    Do NOT use this for general internet queries — use web_search instead.
    """
    results = _retrieval_agent.retrieve(query, top_k=top_k)
    if not results:
        return "No relevant documents found in company knowledge base."

    formatted = []
    for r in results:
        formatted.append(
            f"[Source: {r['metadata'].get('source_file', 'unknown')} | "
            f"Score: {r['similarity_score']}]\n{r['content']}"
        )
    return "\n\n---\n\n".join(formatted)


# ── Web search ────────────────────────────────────────────────────────────────

@tool
def web_search(query: str, num_results: int = 5) -> str:
    """
    Search the web for current information not available in internal documents.
    Use for recent news, facts, or any topic requiring up-to-date external data.
    """
    result = _web_search(query, num_results=num_results)
    return result.get("raw_text") or result.get("error", "No results.")


# ── Email ─────────────────────────────────────────────────────────────────────

@tool
def send_email(to: str, subject: str, body: str, attachment_path: str = None, html: bool = False) -> str:
    """
    Send an email via Gmail to one or more recipients.
    Supports optional file attachments (PDF, DOCX, TXT).
    Combine with summarize_and_export to send generated reports by email.
    """
    result = _send_email(to=to, subject=subject, body=body, attachment_path=attachment_path, html=html)
    return result.get("message", str(result))


# ── Summarize / export ────────────────────────────────────────────────────────

@tool
def summarize_and_export(content: str, title: str = "Summary Report", format: str = "pdf", save_dir: str = "data/reports") -> str:
    """
    Summarize content and export it as a downloadable file.
    Supports PDF, DOCX, and TXT formats.
    Use when the user wants a document or report they can download or email.
    """
    result = _summarize_and_export(content=content, title=title, format=format, save_dir=save_dir)
    return result.get("message") or result.get("error", str(result))


# ── CSV tools ─────────────────────────────────────────────────────────────────

@tool
def csv_preview(file_path: str, num_rows: int = 5) -> str:
    """Load and preview a CSV file — shows shape, column names, data types, and first N rows."""
    import json
    return json.dumps(_csv_preview(file_path, num_rows), default=str)

@tool
def csv_summary_stats(file_path: str, columns: list = None) -> str:
    """Generate summary statistics for numeric columns in a CSV file."""
    import json
    return json.dumps(_csv_summary_stats(file_path, columns), default=str)

@tool
def csv_filter(file_path: str, column: str, operator: str, value: str, export_path: str = None) -> str:
    """
    Filter rows in a CSV file by a condition.
    Operators: ==, !=, >, <, >=, <=, contains.
    """
    import json
    return json.dumps(_csv_filter(file_path, column, operator, value, export_path), default=str)

@tool
def csv_export_analysis(file_path: str, format: str = "pdf", save_dir: str = "data/reports") -> str:
    """Run full analysis on a CSV and export as PDF, DOCX, or TXT report."""
    import json
    return json.dumps(_csv_export_analysis(file_path, format, save_dir), default=str)


# ── Reminder tools ────────────────────────────────────────────────────────────

@tool
def add_reminder(title: str, fire_at: str, note: str = "", email: str = None, recurrence: str = None) -> str:
    """
    Schedule a reminder at a specific date and time.
    Delivers via email or console. Supports one-time and recurring (cron) reminders.
    Use when the user says 'remind me', 'set a reminder', or 'alert me at'.
    """
    import json
    return json.dumps(_add_reminder(title=title, fire_at=fire_at, note=note, email=email, recurrence=recurrence), default=str)

@tool
def list_reminders(status: str = None) -> str:
    """List all scheduled reminders. Optionally filter by status: pending, fired, or cancelled."""
    result = _list_reminders(status=status)
    return result.get("summary") or result.get("message", "No reminders found.")

@tool
def cancel_reminder(reminder_id: str) -> str:
    """Cancel a pending reminder by its ID."""
    result = _cancel_reminder(reminder_id=reminder_id)
    return result.get("message", str(result))


# ── All tools list ────────────────────────────────────────────────────────────

ALL_LC_TOOLS = [
    search_company_docs,
    web_search,
    send_email,
    summarize_and_export,
    csv_preview,
    csv_summary_stats,
    csv_filter,
    csv_export_analysis,
    add_reminder,
    list_reminders,
    cancel_reminder,
]