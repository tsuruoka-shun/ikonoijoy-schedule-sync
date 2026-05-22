import logging
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

JST = ZoneInfo("Asia/Tokyo")
today = datetime.now(JST).date()
year = today.year
month = today.month

urls = {
    "equal_love": "https://equal-love.jp",
    "not_equal_me": "https://not-equal-me.jp",
    "nearly_equal_joy": "https://nearly-equal-joy.jp",
}

schedules: dict[str, list[dict[str, str]]] = {
    "equal_love": [],
    "not_equal_me": [],
    "nearly_equal_joy": [],
}


def get_schedule() -> dict[str, list[dict[str, str]]]:
    for group_name, url in urls.items():
        try:
            response = requests.get(
                f"{url}/schedule/calender/{year}/{month:02}", timeout=10
            )
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
        except requests.RequestException:
            logger.exception("%s: Failed request", group_name)
            continue

        cells = soup.select(".calendarBody .cell")
        if not cells:
            raise RuntimeError(f"Failed to get cells (group: {group_name})")

        for cell in cells:
            date_tag = cell.select_one(".date")
            if not date_tag or not date_tag.text.strip():
                continue

            date_text = date_tag.text.strip()
            acquisition_date = date(year, month, int(date_text))
            if today - timedelta(days=7) > acquisition_date:
                continue

            for div_tag in cell.select("div[class^=live]"):
                title_tag = div_tag.select_one(".tit")
                if not title_tag:
                    logger.warning("Failed to get title (group: %s)", group_name)
                    continue

                link_tag = div_tag.select_one("a")
                if not link_tag:
                    continue

                href = link_tag.get("href")
                if not isinstance(href, str):
                    continue

                schedules[group_name].append(
                    {
                        "date": acquisition_date.strftime("%Y-%m-%d"),
                        "title": title_tag.text.strip(),
                        "link": f"{url}{href}",
                    }
                )
        logger.debug("Scraped %d events", len(schedules[group_name]))
    return schedules
