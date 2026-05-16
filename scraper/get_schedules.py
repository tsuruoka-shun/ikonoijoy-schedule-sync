import logging
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

jst = timezone(timedelta(hours=9), "JST")
now = datetime.now(jst)
year = now.year
month = f"{now.month:02}"

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


def get_schedules() -> dict[str, list[dict[str, str]]]:
    for group_name, url in urls.items():
        try:
            response = requests.get(
                f"{url}/schedule/calender/{year}/{month}", timeout=10
            )
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
        except requests.RequestException:
            logger.exception("%s: Failed request", group_name)
            continue

        cells = soup.select(".calendarBody .cell")
        if not cells:
            logger.warning("%s: Failed to get cell", group_name)
            continue

        for cell in cells:
            date_tag = cell.select_one(".date")
            if not date_tag or not date_tag.text.strip():
                continue

            date = date_tag.text.strip()

            for item in cell.select("div[class^=live]"):
                title_tag = item.select_one(".tit")
                if not title_tag:
                    logger.warning("%s: Failed to get title", group_name)
                    continue

                link_tag = item.select_one("a")
                if not link_tag:
                    continue

                href = link_tag.get("href")
                if not isinstance(href, str):
                    continue

                schedules[group_name].append(
                    {
                        "date": f"{year}-{month}-{int(date):02}",
                        "title": title_tag.text.strip(),
                        "link": f"{url}{href}",
                    }
                )
        logger.info(
            "Scraped %d events (group: %s)", len(schedules[group_name]), group_name
        )
    return schedules
