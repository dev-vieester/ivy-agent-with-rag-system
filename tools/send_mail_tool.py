import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import Optional


def send_email(
    to: str,
    subject: str,
    body: str,
    attachment_path: Optional[str] = None,
    html: bool = False,
) -> dict:
    """
    Send an email via Gmail SMTP, with optional file attachment.

    Args:
        to:               Recipient email address (or comma-separated list)
        subject:          Email subject line
        body:             Email body — plain text or HTML
        attachment_path:  Optional path to a file to attach (PDF, DOCX, TXT, etc.)
        html:             If True, send body as HTML

    Returns:
        dict with 'success' bool and 'message' string
    """
    sender = os.getenv("GMAIL_SENDER")
    password = os.getenv("GMAIL_APP_PASSWORD")

    if not sender or not password:
        return {
            "success": False,
            "message": "GMAIL_SENDER or GMAIL_APP_PASSWORD not set in .env",
        }

    # Validate attachment exists
    if attachment_path and not Path(attachment_path).exists():
        return {
            "success": False,
            "message": f"Attachment not found: {attachment_path}",
        }

    try:
        msg = MIMEMultipart()
        msg["From"] = sender
        msg["To"] = to
        msg["Subject"] = subject

        # Body
        content_type = "html" if html else "plain"
        msg.attach(MIMEText(body, content_type))

        # Attachment
        if attachment_path:
            file_path = Path(attachment_path)
            with open(file_path, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename={file_path.name}",
            )
            msg.attach(part)

        # Send
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            recipients = [r.strip() for r in to.split(",")]
            server.sendmail(sender, recipients, msg.as_string())

        attachment_note = f" with attachment '{Path(attachment_path).name}'" if attachment_path else ""
        return {
            "success": True,
            "message": f"Email sent to {to}{attachment_note}",
            "to": to,
            "subject": subject,
        }

    except smtplib.SMTPAuthenticationError:
        return {
            "success": False,
            "message": (
                "Gmail authentication failed. "
                "Make sure you are using an App Password (not your regular Gmail password). "
                "Enable 2FA and generate one at: myaccount.google.com/apppasswords"
            ),
        }
    except smtplib.SMTPException as e:
        return {"success": False, "message": f"SMTP error: {e}"}
    except Exception as e:
        return {"success": False, "message": f"Failed to send email: {e}"}


# Claude tool schema
SEND_EMAIL_TOOL_SCHEMA = {
    "name": "send_email",
    "description": (
        "Send an email via Gmail to one or more recipients. "
        "Supports optional file attachments (PDF, DOCX, TXT). "
        "Combine with summarize_and_export to send generated reports by email."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "to": {
                "type": "string",
                "description": "Recipient email address. Use comma-separation for multiple recipients.",
            },
            "subject": {
                "type": "string",
                "description": "Email subject line",
            },
            "body": {
                "type": "string",
                "description": "Email body text. Can be plain text or HTML if html=true.",
            },
            "attachment_path": {
                "type": "string",
                "description": "Optional: full file path to attach to the email (e.g. data/reports/report.pdf)",
            },
            "html": {
                "type": "boolean",
                "description": "Set to true if the body contains HTML markup",
                "default": False,
            },
        },
        "required": ["to", "subject", "body"],
    },
}