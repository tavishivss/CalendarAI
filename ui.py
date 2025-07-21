import streamlit as st
from summarize_utils import call_gpt_summary
from google.oauth2.credentials import Credentials
from datetime import datetime, timedelta, time
from dateutil import parser
from dotenv import load_dotenv
import openai
import os
import asyncio
import re
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import CallToolResult

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=openai_api_key)

async def call_tool(server_file, tool_name, inputs):
    server_params = StdioServerParameters(command="python", args=[server_file])
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            return await session.call_tool(tool_name, inputs)

def check_holiday(date_str):
    return asyncio.run(call_tool("holiday_server.py", "is_holiday", {"date": date_str}))

def find_common_time(emails, start, end, duration):
    print("🧪 Checking mutual availability for:", emails)
    try:
        result = asyncio.run(call_tool("calendar_server.py", "find_common_free_time", {
            "participants": emails,
            "date_range": (start, end),
            "duration": duration
        }))
        print(f"📬 Tool response: {result}")

        if isinstance(result, CallToolResult) and result.content:
            return result.content[0].text
        elif isinstance(result, str) and "No common free time" not in result:
            return result

        return "No common free time found."
    except Exception as e:
        print(f"❌ Failed to check common availability: {e}")
        return "No common free time found."

def create_calendar_event(start, summary, duration, attendees):
    print("🔥 Calling calendar tool to create event")
    return asyncio.run(call_tool("calendar_server.py", "create_event", {
        "date": start,
        "summary": summary,
        "duration": duration,
        "attendees": attendees
    }))

st.set_page_config(page_title="Meeting Whisperer", page_icon="🧠")
st.title("🧠 Meeting Whisperer Assistant")

emails_input = st.text_area("📧 Enter participant emails (comma-separated)")
uploaded_file = st.file_uploader("📄 Upload meeting transcript (.txt)", type="txt")

if uploaded_file and emails_input:
    transcript = uploaded_file.read().decode("utf-8")
    emails = [e.strip() for e in emails_input.split(",") if e.strip()]
    if st.button("🧠 Generate Summary & Check Availability"):
        with st.spinner("Working on it..."):
            try:
                result = call_gpt_summary(transcript)
                st.session_state.summary_result = result
                st.session_state.emails = emails
            except Exception as e:
                st.error(f"Summarization failed: {e}")

if "summary_result" in st.session_state:
    result = st.session_state.summary_result
    emails = st.session_state.emails

    st.subheader("📋 Summary")
    st.write(result["summary"])

    st.subheader("✅ Action Items")
    st.write(result["action_items"])

    next_meeting = result.get("next_meeting")
    suggested_date = None

    if next_meeting:
        st.subheader("🗓️ Suggested Next Meeting")
        try:
            date_match = re.search(r"\b(?:\w+ \d{1,2}, \d{4}|\d{4}-\d{2}-\d{2})\b", next_meeting)
            if date_match:
                parsed_date = parser.parse(date_match.group())
                suggested_date = parsed_date.replace(hour=9, minute=0)
                st.session_state.suggested_date = suggested_date
                st.success(f"GPT Suggests: {suggested_date.strftime('%Y-%m-%d %I:%M %p')}")
        except Exception:
            st.warning("Could not parse suggested meeting date.")

    st.subheader("🔍 Find Common Time")
    duration = st.number_input("Duration (hours)", min_value=1, max_value=4, value=1)
    date_range = st.date_input("Preferred Date Range", value=(datetime.today(), datetime.today() + timedelta(days=7)))
    manual_date = st.date_input("Pick a meeting date", value=st.session_state.get("suggested_date", datetime.now()))
    manual_time = st.time_input("Pick a meeting time (8 AM to 5 PM)", value=time(9, 0))
    manual_datetime = datetime.combine(manual_date, manual_time)

    if st.button("🕒 Check Availability & Holiday", key="check_avail"):
        with st.spinner("Checking everyone's calendar and holiday status..."):
            try:
                start_range = str(datetime.combine(date_range[0], time(8, 0)).isoformat())
                end_range = str(datetime.combine(date_range[1], time(17, 0)).isoformat())
                common_slot = find_common_time(emails, start_range, end_range, duration)
                st.session_state.common_slot = common_slot

                holiday_name = check_holiday(manual_datetime.date().isoformat())

                if isinstance(holiday_name, CallToolResult) and getattr(holiday_name, "content", []):
                    try:
                        name = holiday_name.content[0].text if hasattr(holiday_name.content[0], "text") else None
                        if name:
                            st.error(f"❌ {manual_datetime.date()} is a holiday: {name}")
                        else:
                            st.error(f"❌ {manual_datetime.date()} is a holiday")
                    except Exception:
                        st.error(f"❌ {manual_datetime.date()} is a holiday")
                else:
                    st.info(f"📆 {manual_datetime.date()} is not a holiday.")
            except Exception as e:
                st.error(f"Failed to check availability or holidays: {e}")

    # Only show if common_slot was set
    if "common_slot" in st.session_state:
        common_slot = st.session_state.common_slot

        if common_slot == "No common free time found.":
            st.warning("No common time available for the selected date range.")
        else:
            try:
                mutual_dt = datetime.fromisoformat(common_slot)
                st.success(f"✅ Mutual free slot found: {mutual_dt.strftime('%Y-%m-%d %I:%M %p')}")
            except Exception:
                st.success(f"✅ Mutual free slot found: {common_slot}")

            st.info(f"🕓 You selected: {manual_datetime.strftime('%Y-%m-%d %I:%M %p')}")

            if st.button("📅 Create Invite at Mutual Time", key="create_mutual"):
                print("🔥 Calling calendar tool to create event at mutual time")
                try:
                    link = create_calendar_event(common_slot, result["summary"], duration, emails)
                    st.success(f"📨 Event Created: [View on Google Calendar]({link})")
                except Exception as e:
                    st.error(f"❌ Failed to create event: {e}")
