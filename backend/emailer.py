"""Sends the password reset email (SRS FR1.3) through any SMTP service (e.g. Gmail).

Settings come from environment variables, so no password is stored in the code:
  SMTP_HOST      e.g. smtp.gmail.com
  SMTP_PORT      e.g. 587
  SMTP_USER      the email address that sends the mail
  SMTP_PASSWORD  its password (for Gmail: an "App password")
"""
import os
import smtplib
from email.message import EmailMessage


def email_is_set_up():
    return bool(os.environ.get("SMTP_HOST") and os.environ.get("SMTP_USER") and os.environ.get("SMTP_PASSWORD"))


def send_reset_email(to_address, link):
    """Returns True if the email was sent, False if it was not."""
    if not email_is_set_up():
        return False

    message = EmailMessage()
    message["Subject"] = "Reset your NextFit password"
    message["From"] = os.environ["SMTP_USER"]
    message["To"] = to_address
    message.set_content(
        "Hello,\n\n"
        "Use this link to choose a new password (it works for 1 hour):\n"
        f"{link}\n\n"
        "If you did not ask for this, you can ignore this email.\n\nNextFit")

    try:
        with smtplib.SMTP(os.environ["SMTP_HOST"], int(os.environ.get("SMTP_PORT", "587")), timeout=15) as server:
            server.starttls()
            server.login(os.environ["SMTP_USER"], os.environ["SMTP_PASSWORD"])
            server.send_message(message)
        return True
    except Exception as error:
        print("Could not send email:", error)
        return False
