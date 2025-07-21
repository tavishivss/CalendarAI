import openai
import re
import os
from dotenv import load_dotenv
load_dotenv()

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def call_gpt_summary(transcript: str) -> dict:
    prompt = f"""
You are a meeting assistant. Given the transcript below, return:
1. A short summary.
2. Action items for each person.
3. The next suggested meeting time (if mentioned).

Transcript:
{transcript}
"""
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )

    content = response.choices[0].message.content
    return parse_summary_output(content)


def parse_summary_output(text: str) -> dict:
    summary_match = re.search(r"1\.\s*.*?\n(.*?)(?=\n2\.)", text, re.DOTALL)
    actions_match = re.search(r"2\.\s*.*?\n(.*?)(?=\n3\.)", text, re.DOTALL)
    next_meeting_match = re.search(r"3\.\s*.*?\n(.*)", text, re.DOTALL)

    return {
        "summary": summary_match.group(1).strip() if summary_match else "",
        "action_items": actions_match.group(1).strip() if actions_match else "",
        "next_meeting": next_meeting_match.group(1).strip() if next_meeting_match else "",
    }
