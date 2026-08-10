import os
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Recipient
RECIPIENT = "nivasanmugam@gmail.com"

# Check environment or prompt for SMTP credentials
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "nivasanmugam@gmail.com")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD", "faxw uqwy vqmw cmcw")
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))

def send_latest_report():
    latest_html_path = os.path.join(os.path.dirname(__file__), "reports", "latest_daily_report.html")

    if not os.path.exists(latest_html_path):
        print("Error: latest_daily_report.html not found.")
        return False

    with open(latest_html_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    if not SENDER_PASSWORD:
        print("SMTP SENDER_PASSWORD environment variable is missing.")
        print(f"Report is compiled for {RECIPIENT} and saved at: {latest_html_path}")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "🚀 Immediate Job Application Summary Report (14 Azure & Cloud Jobs)"
        msg["From"] = SENDER_EMAIL
        msg["To"] = RECIPIENT
        msg.attach(MIMEText(html_content, "html"))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECIPIENT, msg.as_string())

        print(f"Successfully sent summary email to {RECIPIENT}!")
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

if __name__ == "__main__":
    send_latest_report()
