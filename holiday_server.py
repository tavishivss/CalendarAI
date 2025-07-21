from mcp.server.fastmcp import FastMCP

import requests

mcp = FastMCP("Holiday Checker")

@mcp.tool()
def is_holiday(date: str, country_code: str = "US") -> str | None:
    """
    Return the name of the holiday if the date is a public holiday.
    Otherwise, return None.
    """
    try:
        year = date[:4]
        response = requests.get(f"https://date.nager.at/api/v3/PublicHolidays/{year}/{country_code}")
        if response.status_code != 200:
            return None
        holidays = response.json()
        for holiday in holidays:
            if holiday["date"] == date:
                return holiday["localName"]
        return None
    except Exception:
        return None

if __name__ == "__main__":
    mcp.run()
