import os
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import google.auth.exceptions
import json

SCOPES = ["https://www.googleapis.com/auth/calendar"]
TOKENS_DIR = "tokens"

if not os.path.exists(TOKENS_DIR):
    os.makedirs(TOKENS_DIR)

def main():
    email = input("Enter your Google email address: ").strip()
    if not email:
        print("❌ Email address required.")
        return

    flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
    creds = flow.run_local_server(port=0)

    token_path = os.path.join(TOKENS_DIR, f"{email}.json")
    with open(token_path, "w") as token_file:
        token_file.write(creds.to_json())
    print(f"✅ Token saved for {email} → {token_path}")

if __name__ == "__main__":
    main()

