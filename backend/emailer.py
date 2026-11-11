"""Sends the password reset email (SRS FR1.3).

There are two ways to send, chosen by which settings exist (environment variables,
so no password is stored in the code):

1. Brevo (used on the live site). It sends over normal HTTPS, so it also works on
   hosts that block the usual email ports, and it can reach any email address.
     BREVO_API_KEY    the API key from your Brevo account
     EMAIL_FROM       the sending address on your own domain, e.g. noreply@karega.tech
     EMAIL_FROM_NAME  (optional) the sender name people see, default "NextFit"

2. SMTP (handy on your own computer, e.g. with a Gmail account).
     SMTP_HOST      e.g. smtp.gmail.com
     SMTP_PORT      e.g. 587
     SMTP_USER      the email address that sends the mail
     SMTP_PASSWORD  its password (for Gmail: an "App password")

If both are set, Brevo is used.
"""
import json
import os
import smtplib
import urllib.request
from email.message import EmailMessage

BREVO_URL = "https://api.brevo.com/v3/smtp/email"
SUBJECT = "Reset your NextFit password"


def brevo_is_set_up():
    return bool(os.environ.get("BREVO_API_KEY") and os.environ.get("EMAIL_FROM"))


def smtp_is_set_up():
    return bool(os.environ.get("SMTP_HOST") and os.environ.get("SMTP_USER") and os.environ.get("SMTP_PASSWORD"))


def email_is_set_up():
    return brevo_is_set_up() or smtp_is_set_up()


def reset_text(link):
    return ("Hello,\n\n"
            "Use this link to choose a new password (it works for 1 hour):\n"
            f"{link}\n\n"
            "If you did not ask for this, you can ignore this email.\n\nNextFit")


def send_with_brevo(to_address, link):
    """Ask Brevo to send the email. Brevo answers with a 2xx code when it accepts it."""
    body = {
        "sender": {"name": os.environ.get("EMAIL_FROM_NAME", "NextFit"), "email": os.environ["EMAIL_FROM"]},
        "to": [{"email": to_address}],
        "subject": SUBJECT,
        "textContent": reset_text(link),
    }
    request = urllib.request.Request(
        BREVO_URL, data=json.dumps(body).encode("utf-8"), method="POST",
        headers={"api-key": os.environ["BREVO_API_KEY"],
                 "content-type": "application/json", "accept": "application/json"})
    with urllib.request.urlopen(request, timeout=15) as response:
        return 200 <= response.status < 300


def send_with_smtp(to_address, link):
    message = EmailMessage()
    message["Subject"] = SUBJECT
    message["From"] = os.environ["SMTP_USER"]
    message["To"] = to_address
    message.set_content(reset_text(link))
    with smtplib.SMTP(os.environ["SMTP_HOST"], int(os.environ.get("SMTP_PORT", "587")), timeout=15) as server:
        server.starttls()
        server.login(os.environ["SMTP_USER"], os.environ["SMTP_PASSWORD"])
        server.send_message(message)
    return True


def send_reset_email(to_address, link):
    """Returns True if the email was sent, False if it was not."""
    if not email_is_set_up():
        return False
    try:
        if brevo_is_set_up():
            return send_with_brevo(to_address, link)
        return send_with_smtp(to_address, link)
    except Exception as error:
        # urllib errors carry Brevo's explanation in the response body; print it to the server log.
        details = error.read().decode("utf-8", "replace") if hasattr(error, "read") else ""
        print("Could not send email:", error, details)
        return False
