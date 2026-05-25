import logging
import random
import time
from datetime import date, datetime
from typing import Optional, TypedDict
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class ScrapEvent(TypedDict):
    date: str
    title: str
    link: str


def get_time_bounds(zone_time: str = "Asia/Tokyo") -> tuple[date, int, int]:
    tz = ZoneInfo(zone_time)
    today = datetime.now(tz).date()
    year = today.year
    month = today.month
    return (
        today,
        year,
        month,
    )


def fetch_retry(
    url: str,
    year: int,
    month: int,
    max_retries: int = 3,
    backoff_base: float = 2.0,
) -> Optional[requests.Response]:
    absolute_url = f"{url}/schedule/calender/{year}/{month:02}"

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(
                absolute_url,
                timeout=(5, 10),
            )
            response.raise_for_status()
            return response

        except requests.exceptions.Timeout:
            logger.warning(f"[{attempt}/{max_retries}] Timeout: {absolute_url}")

        except requests.exceptions.ConnectionError:
            logger.warning(
                f"[{attempt}/{max_retries}] Connection error: {absolute_url}"
            )

        except requests.exceptions.HTTPError as e:
            status = e.response.status_code

            if 400 <= status < 500:
                logger.error(f"Client error {status}: {absolute_url}")
                return None

            logger.warning(
                f"[{attempt}/{max_retries}] Server error {status}: {absolute_url}"
            )

        if attempt < max_retries:
            wait = backoff_base**attempt + random.uniform(0, 1)

            logger.debug(f"Retry after {wait:.1f}s")

            time.sleep(wait)

    logger.error(f"Max retries reached: {absolute_url}")
    return None


def get_schedule() -> dict[str, list[ScrapEvent]]:
    GROUP_URLS = {
        "equal_love": "https://equal-love.jp",
        "not_equal_me": "https://not-equal-me.jp",
        "nearly_equal_joy": "https://nearly-equal-joy.jp",
    }

    schedules_by_group: dict[str, list[ScrapEvent]] = {
        "equal_love": [],
        "not_equal_me": [],
        "nearly_equal_joy": [],
    }

    today, year, month = get_time_bounds()

    for group_name, url in GROUP_URLS.items():
        try:
            response = fetch_retry(url, year, month)
            if response is None:
                logger.error("Failed to fetch schedule (group: %s)", group_name)
                continue

            soup = BeautifulSoup(response.text, "html.parser")
        except Exception:
            logger.exception("Failed request (group: %s)", group_name)
            continue

        cell_divs = soup.select(".calendarBody .cell")
        if not cell_divs:
            raise RuntimeError(f"Failed to get cells (group: {group_name})")

        for cell_div in cell_divs:
            date_span = cell_div.select_one(".date")
            if not date_span or not date_span.text.strip():
                continue

            day_number = int(date_span.text.strip())
            event_date = date(year, month, day_number)

            if event_date < today:
                continue

            for live_divs in cell_div.select("div[class^=live]"):
                tit_span = live_divs.select_one(".tit")
                if not tit_span:
                    logger.warning("Failed to get title (group: %s)", group_name)
                    continue

                link_a = live_divs.select_one("a")
                if not link_a:
                    continue

                href = link_a.get("href")
                if not isinstance(href, str):
                    continue

                schedules_by_group[group_name].append(
                    {
                        "date": event_date.strftime("%Y-%m-%d"),
                        "title": tit_span.text.strip(),
                        "link": f"{url}{href}",
                    }
                )
        logger.debug(
            "Scraped %d events for %s",
            len(schedules_by_group[group_name]),
            group_name,
        )

    return schedules_by_group
