from tools.web_search_tool import web_search, WEB_SEARCH_TOOL_SCHEMA
from tools.summarize_export_tool import summarize_and_export, SUMMARIZE_EXPORT_TOOL_SCHEMA
from tools.send_mail_tool import send_email, SEND_EMAIL_TOOL_SCHEMA
from tools.csv_analyzer import (
    csv_preview, csv_summary_stats, csv_filter, csv_export_analysis,
    CSV_PREVIEW_SCHEMA, CSV_SUMMARY_STATS_SCHEMA, CSV_FILTER_SCHEMA, CSV_EXPORT_SCHEMA,
)
from tools.reminder_tool import (
    add_reminder, list_reminders, cancel_reminder,
    ADD_REMINDER_SCHEMA, LIST_REMINDERS_SCHEMA, CANCEL_REMINDER_SCHEMA,
)

# Maps tool name → callable function
TOOL_FUNCTIONS = {
    # Web
    "web_search": web_search,
    # Documents
    "summarize_and_export": summarize_and_export,
    # Email
    "send_email": send_email,
    # CSV
    "csv_preview": csv_preview,
    "csv_summary_stats": csv_summary_stats,
    "csv_filter": csv_filter,
    "csv_export_analysis": csv_export_analysis,
    # Reminders
    "add_reminder": add_reminder,
    "list_reminders": list_reminders,
    "cancel_reminder": cancel_reminder,
}

# All schemas passed to Claude
ALL_TOOL_SCHEMAS = [
    WEB_SEARCH_TOOL_SCHEMA,
    SUMMARIZE_EXPORT_TOOL_SCHEMA,
    SEND_EMAIL_TOOL_SCHEMA,
    CSV_PREVIEW_SCHEMA,
    CSV_SUMMARY_STATS_SCHEMA,
    CSV_FILTER_SCHEMA,
    CSV_EXPORT_SCHEMA,
    ADD_REMINDER_SCHEMA,
    LIST_REMINDERS_SCHEMA,
    CANCEL_REMINDER_SCHEMA,
]