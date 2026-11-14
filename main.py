import os
import sys
import time
import ssl
import smtplib
import requests
from email.message import EmailMessage

API_URL = "https://api.gold-api.com/price/XAU/USD"

def get_xau_price():
    try:
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        return {
            "price": float(data["price"]),
            "updated_at": data.get("updatedAt", "N/A")
        }
    except requests.RequestException as e:
        print(f"API request failed: {e}")
        return None

def send_email_alert(subject, body):
    sender = os.environ.get("SENDER_EMAIL", "").strip()
    password = os.environ.get("GMAIL_APP_PASSWORD", "").replace(" ", "").strip()
    recipient = os.environ.get("RECIPIENT_EMAIL", sender).strip()

    if not sender or not password:
        raise ValueError("Missing SENDER_EMAIL or SENDER_PASSWORD environment variables.")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient
    msg.set_content(body)

    context = ssl.create_default_context()
    # Use smtplib.SMTP (NOT SMTP_SSL) for port 587
    with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()
        server.login(sender, password)
        server.send_message(msg)

def run_once():
    gold_data = get_xau_price()
    if not gold_data:
        return

    current_price = gold_data["price"]
    updated_at = gold_data["updated_at"]

    subject = f"XAU/USD Update: ${current_price:,.2f}"
    body = (
        f"Current Gold (XAU/USD) Price: ${current_price:,.2f} per troy ounce\n"
        f"Last Updated (UTC): {updated_at}"
    )

    send_email_alert(subject, body)
    print(f"Sent update: ${current_price:,.2f}")

if __name__ == "__main__":
    # Pass "--test" to run every 60 seconds for 5 iterations (5 minutes total)
    if "--test" in sys.argv:
        for i in range(5):
            print(f"--- Test run {i + 1}/5 ---")
            run_once()
            if i < 4:
                time.sleep(60)
    else:
        run_once()
