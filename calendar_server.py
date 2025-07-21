from mcp.server.fastmcp import FastMCP
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import os

mcp = FastMCP("Calendar Assistant")
SCOPES = ["https://www.googleapis.com/auth/calendar"]
TOKENS_DIR = "tokens"

def load_user_service(user_email):
    token_path = os.path.join(TOKENS_DIR, f"{user_email}.json")
    if not os.path.exists(token_path):
        raise FileNotFoundError(f"No token found for {user_email}")
    creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    return build("calendar", "v3", credentials=creds)

@mcp.tool()
def create_event(date: str, summary: str, duration: int = 1, attendees: list[str] = []) -> str:
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    service = build("calendar", "v3", credentials=creds)

    start = datetime.fromisoformat(date)
    end = start + timedelta(hours=duration)

    event = {
        "summary": summary,
        "start": {"dateTime": start.isoformat(), "timeZone": "America/New_York"},
        "end": {"dateTime": end.isoformat(), "timeZone": "America/New_York"},
        "attendees": [{"email": email} for email in attendees],
    }

    try:
        created_event = service.events().insert(
            calendarId="primary", body=event, sendUpdates="all"
        ).execute()
        print("✅ Event created successfully.")
        return created_event.get("htmlLink")
    except Exception as e:
        print(f"❌ Failed to create event: {e}")
        return "Error creating event"

    print("📅 Creating calendar event with:")
    print(f"   Start: {start}")
    print(f"   End: {end}")
    print(f"   Attendees: {attendees}")
    return created_event.get("htmlLink")

@mcp.tool()
def find_common_free_time(participants: list[str], date_range: tuple[str, str], duration: int = 1) -> str:
    all_busy = []

    for email in participants:
        try:
            service = load_user_service(email)
            start_time = datetime.fromisoformat(date_range[0])
            end_time = datetime.fromisoformat(date_range[1])

            body = {
                "timeMin": start_time.isoformat(),
                "timeMax": end_time.isoformat(),
                "timeZone": "America/New_York",
                "items": [{"id": email}]
            }

            result = service.freebusy().query(body=body).execute()
            busy = result["calendars"][email].get("busy", [])

            print(f"📬 Busy blocks for {email}:")
            for b in busy:
                print(f"   ⏰ {b['start']} to {b['end']}")

            for b in busy:
                b_start = datetime.fromisoformat(str(b["start"]))
                b_end = datetime.fromisoformat(str(b["end"]))
                all_busy.append((b_start, b_end))
        except Exception as e:
            print(f"❌ Failed for {email}: {e}")

    all_busy.sort(key=lambda x: x[0])

    search_start = datetime.fromisoformat(date_range[0]).replace(hour=8, minute=0)
    search_end = datetime.fromisoformat(date_range[1]).replace(hour=17, minute=0)

    print("📦 Merged busy slots:")
    for b in all_busy:
        print(f"   ❌ {b[0]} to {b[1]}")
    print(f"🕵️ Searching between: {search_start} and {search_end}")

    current = search_start
    while current + timedelta(hours=duration) <= search_end:
        proposed_end = current + timedelta(hours=duration)
        overlap = any(not (proposed_end <= b_start or current >= b_end) for b_start, b_end in all_busy)
        if not overlap:
            return current.isoformat()
        current += timedelta(minutes=30)

    return "No common free time found."

if __name__ == "__main__":
    mcp.run()
