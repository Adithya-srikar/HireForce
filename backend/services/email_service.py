"""
Email service.

If SMTP_HOST / SMTP_USER / SMTP_PASSWORD are set in .env, emails are
sent via SMTP. Otherwise the email is printed to stdout (console stub).
"""
import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)

_SMTP_HOST = os.getenv("SMTP_HOST", "")
_SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
_SMTP_USER = os.getenv("SMTP_USER", "")
_SMTP_PASS = os.getenv("SMTP_PASSWORD", "")
_EMAIL_FROM = os.getenv("EMAIL_FROM", "HireForce <noreply@hireforce.ai>")


def send_email(to: str, subject: str, html_body: str) -> None:
    """Send an HTML email. Falls back to console logging if SMTP is not configured."""
    if not _SMTP_HOST or not _SMTP_USER or not _SMTP_PASS:
        logger.info(
            "[EMAIL STUB] To: %s | Subject: %s\n%s",
            to, subject, html_body,
        )
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = _EMAIL_FROM
    msg["To"] = to
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(_SMTP_HOST, _SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(_SMTP_USER, _SMTP_PASS)
            server.sendmail(_EMAIL_FROM, to, msg.as_string())
        logger.info("Email sent to %s | Subject: %s", to, subject)
    except Exception as exc:
        logger.error("Failed to send email to %s: %s", to, exc)


def send_interview_invite(
    candidate_name: str,
    candidate_email: str,
    job_title: str,
    interview_date: str,
    interview_time: str,
    interview_link: str,
) -> None:
    """Send an interview invite to a candidate."""
    subject = f"Interview Invitation – {job_title} | HireForce"
    html_body = f"""
    <h2>Hi {candidate_name},</h2>
    <p>Congratulations! You have been selected for an interview for the position of
    <strong>{job_title}</strong>.</p>
    <p><strong>Date:</strong> {interview_date}<br>
    <strong>Time:</strong> {interview_time}</p>
    <p>Click the link below to start your interview when it's time:</p>
    <p><a href="{interview_link}" style="padding:10px 20px;background:#6c47ff;color:#fff;
    border-radius:6px;text-decoration:none;">Start Interview</a></p>
    <p>Best of luck!<br>– The HireForce Team</p>
    """
    send_email(candidate_email, subject, html_body)
