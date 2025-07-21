from mcp.server.fastmcp import FastMCP
from summarize_utils import call_gpt_summary

mcp = FastMCP("Meeting Whisperer")


@mcp.tool()
def summarize_transcript(transcript: str) -> dict:
    return call_gpt_summary(transcript)


if __name__ == "__main__":
    mcp.run()
