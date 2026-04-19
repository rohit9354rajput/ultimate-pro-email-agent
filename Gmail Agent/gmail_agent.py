# ==========================================================
# ULTIMATE PRO EMAIL AGENT
# Student + Common Person + Smart LLM Gmail Auto Reply Agent
# Gmail + Ollama (phi3 / llama3 / mistral)
# ==========================================================
# FEATURES
# ----------------------------------------------------------
# ✔ Reads unread Gmail inbox mails
# ✔ Ignores promotions / spam / OTP / newsletters
# ✔ Detects urgent mails first
# ✔ Student mode replies
# ✔ Common man personal replies
# ✔ HR / Placement professional replies
# ✔ Teacher / Faculty respectful replies
# ✔ Hindi + English smart replies
# ✔ Fully LLM based natural replies
# ✔ Manual send OR Auto send
# ✔ Local private AI using Ollama
# ==========================================================
# REQUIRED
# ----------------------------------------------------------
# pip install google-api-python-client google-auth-httplib2
# pip install google-auth-oauthlib requests
#
# Put in same folder:
# 1. gmail_agent.py
# 2. credentials.json
#
# Start Ollama:
# ollama run phi3
#
# Run:
# python gmail_agent.py
# ==========================================================

import os
import time
import base64
import pickle
import requests

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


# ==========================================================
# SETTINGS
# ==========================================================
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

AUTO_SEND = True         # True = direct send
MODEL = "phi3"            # phi3 / llama3 / mistral
OLLAMA_URL = "http://localhost:11434/api/generate"

CHECK_INTERVAL = 20       # seconds

SIGNATURE = """

Regards,
Rohit Singh
PGDM Student
"""

# ==========================================================
# GMAIL LOGIN
# ==========================================================
def gmail_auth():

    creds = None

    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as file:
            creds = pickle.load(file)

    if not creds or not creds.valid:

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json",
                SCOPES
            )

            creds = flow.run_local_server(port=0)

        with open("token.pickle", "wb") as file:
            pickle.dump(creds, file)

    return build("gmail", "v1", credentials=creds)


# ==========================================================
# GET SMART EMAILS ONLY
# ==========================================================
def get_unread_emails(service):

    result = service.users().messages().list(
        userId="me",
        q="""
        in:inbox is:unread
        -category:promotions
        -category:social
        -in:spam
        -in:trash
        -subject:otp
        -subject:verification
        -subject:newsletter
        newer_than:5d
        """
    ).execute()

    return result.get("messages", [])


# ==========================================================
# READ EMAIL
# ==========================================================
def read_email(service, msg_id):

    msg = service.users().messages().get(
        userId="me",
        id=msg_id,
        format="full"
    ).execute()

    headers = msg["payload"]["headers"]

    subject = ""
    sender = ""

    for item in headers:

        if item["name"] == "Subject":
            subject = item["value"]

        if item["name"] == "From":
            sender = item["value"]

    body = ""

    try:
        payload = msg["payload"]

        if "parts" in payload:

            for part in payload["parts"]:

                if part["mimeType"] == "text/plain":

                    data = part["body"]["data"]

                    body = base64.urlsafe_b64decode(
                        data
                    ).decode(errors="ignore")

                    break

        else:
            data = payload["body"]["data"]

            body = base64.urlsafe_b64decode(
                data
            ).decode(errors="ignore")

    except:
        body = "Unable to read email."

    return sender, subject, body


# ==========================================================
# DETECT PRIORITY
# ==========================================================
def detect_priority(subject, body):

    text = (subject + " " + body).lower()

    urgent_words = [
        "urgent", "asap", "today", "important",
        "deadline", "immediately", "jaldi",
        "turant", "aaj", "priority"
    ]

    for word in urgent_words:
        if word in text:
            return "URGENT"

    return "NORMAL"


# ==========================================================
# SMART LLM REPLY
# ==========================================================
def generate_reply(subject, email_text):

    text = (subject + " " + email_text).lower()

    # ------------------------------------------------------
    # Detect Role
    # ------------------------------------------------------
    if any(word in text for word in [
        "interview", "job", "resume", "internship",
        "hr", "placement", "recruitment"
    ]):
        role = "professional placement student"

    elif any(word in text for word in [
        "assignment", "faculty", "sir", "maam",
        "professor", "submission", "exam"
    ]):
        role = "respectful academic student"

    elif any(word in text for word in [
        "meeting", "discussion", "schedule"
    ]):
        role = "formal coordination person"

    elif any(word in text for word in [
        "friend", "notes", "class", "buddy"
    ]):
        role = "friendly student"

    else:
        role = "smart common person"

    # ------------------------------------------------------
    # Language Detect
    # ------------------------------------------------------
    hindi_words = [
        "aap", "ji", "kal", "jaldi",
        "namaste", "kripya", "dhanyavad"
    ]

    language = "English"

    for word in hindi_words:
        if word in text:
            language = "Hindi + English"
            break

    # ------------------------------------------------------
    # Prompt
    # ------------------------------------------------------
    prompt = f"""
You are an elite intelligent email assistant.

Reply as:
{role}

Language:
{language}

Rules:
1. Sound human and natural
2. Understand sender intent deeply
3. If urgent -> show priority
4. If professor -> respectful
5. If HR -> confident professional
6. If friend -> casual helpful
7. If complaint -> polite apology
8. Keep concise under 100 words
9. No robotic wording
10. Give best practical response

Subject:
{subject}

Email:
{email_text}

Write only the email reply body.
"""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False
            },
            timeout=120
        )

        reply = response.json()["response"].strip()

        return reply + SIGNATURE

    except:
        return "Thank you for your email. I will get back to you shortly." + SIGNATURE


# ==========================================================
# SEND EMAIL
# ==========================================================
def send_email(service, to, subject, reply):

    message = f"""To: {to}
Subject: Re: {subject}

{reply}
"""

    raw = base64.urlsafe_b64encode(
        message.encode()
    ).decode()

    service.users().messages().send(
        userId="me",
        body={"raw": raw}
    ).execute()


# ==========================================================
# MARK READ
# ==========================================================
def mark_as_read(service, msg_id):

    service.users().messages().modify(
        userId="me",
        id=msg_id,
        body={"removeLabelIds": ["UNREAD"]}
    ).execute()


# ==========================================================
# PROCESS EMAIL
# ==========================================================
def process_email(service, msg_id):

    sender, subject, body = read_email(service, msg_id)

    priority = detect_priority(subject, body)

    print("\n================================================")
    print("NEW EMAIL")
    print("PRIORITY :", priority)
    print("FROM     :", sender)
    print("SUBJECT  :", subject)
    print("================================================")

    reply = generate_reply(subject, body)

    print("\nSUGGESTED REPLY:\n")
    print(reply)

    if AUTO_SEND:

        send_email(service, sender, subject, reply)
        print("Reply Sent Automatically")

    else:

        choice = input("\nSend reply? (y/n): ")

        if choice.lower() == "y":
            send_email(service, sender, subject, reply)
            print("Reply Sent")

        else:
            print("Skipped")

    mark_as_read(service, msg_id)


# ==========================================================
# MAIN LOOP
# ==========================================================
def run_agent():

    service = gmail_auth()

    print("========================================")
    print("ULTIMATE PRO EMAIL AGENT STARTED")
    print("MODEL      :", MODEL)
    print("AUTO SEND  :", AUTO_SEND)
    print("CHECK TIME :", CHECK_INTERVAL)
    print("========================================")

    while True:

        emails = get_unread_emails(service)

        if not emails:
            print("No new important emails...")

        for email in emails:
            process_email(service, email["id"])

        time.sleep(CHECK_INTERVAL)


# ==========================================================
# START
# ==========================================================
if __name__ == "__main__":
    run_agent()