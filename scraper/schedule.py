import logging
import random
import time
from datetime import date, datetime
from typing import Optional, TypedDict
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup
from dateutil.relativedelta import relativedelta

logger = logging.getLogger(__name__)


class ScrapEvent(TypedDict):
    date: str
    title: str
    link: str


def get_current_and_next_months(zone_time: str = "Asia/Tokyo") -> list[tuple[int, int]]:
    tz = ZoneInfo(zone_time)
    today = datetime.now(tz).date()
    next_month = today + relativedelta(months=1)

    return [
        (today.year, today.month),
        (next_month.year, next_month.month),
    ]


def build_schedule_url(url: str, year: int, month: int) -> str:
    return f"{url}/schedule/calender/{year}/{month:02}"


def fetch_retry(
    url: str,
    headers: dict[str, str],
    max_retries: int = 3,
    backoff_base: float = 2.0,
) -> Optional[requests.Response]:
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, headers=headers, timeout=(5, 10))
            response.raise_for_status()
            return response
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            logger.warning(
                "[%s/%s] Request error: %s",
                attempt,
                max_retries,
                url,
            )
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code
            if 400 <= status < 500:
                logger.error(
                    "Client error %s: %s",
                    status,
                    url,
                )
                return None
            logger.warning(
                "[%s/%s] Server error %s: %s",
                attempt,
                max_retries,
                status,
                url,
            )

        if attempt < max_retries:
            wait = backoff_base**attempt + random.uniform(0, 1)
            logger.debug("Retry after %.1fs", wait)
            time.sleep(wait)

    logger.error("Max retries reached: %s", url)
    return None


def parse_cell(
    cell_div,
    year,
    month,
    base_url,
) -> list[ScrapEvent]:
    events: list[ScrapEvent] = []

    date_span = cell_div.select_one(".date")
    if not date_span:
        return events

    try:
        day = int(date_span.text.strip())
        event_date = date(year, month, day)
    except (ValueError, TypeError):
        return events

    for live_div in cell_div.select("div[class^=live]"):
        tit = live_div.select_one(".tit")
        a = live_div.select_one("a")

        if not tit or not a:
            continue

        href = a.get("href")
        if not href:
            continue

        events.append(
            {
                "date": event_date.strftime("%Y-%m-%d"),
                "title": tit.text.strip(),
                "link": f"{base_url}{a['href']}",
            }
        )

    return events


def fetch_group_schedule(
    url: str,
    headers: dict[str, str],
    year: int,
    month: int,
) -> Optional[BeautifulSoup]:
    response = fetch_retry(build_schedule_url(url, year, month), headers)
    if not response:
        return None

    return BeautifulSoup(response.text, "html.parser")


def get_schedule() -> dict[str, list[ScrapEvent]]:
    GROUP_URLS = {
        "equal_love": "https://equal-love.jp",
        "not_equal_me": "https://not-equal-me.jp",
        "nearly_equal_joy": "https://nearly-equal-joy.jp",
    }

    schedules_by_group: dict[str, list[ScrapEvent]] = {key: [] for key in GROUP_URLS}
    target_date = get_current_and_next_months()
    today = datetime.now(ZoneInfo("Asia/Tokyo")).date()
    headers = {
        "user-agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        )
    }

    for group_name, url in GROUP_URLS.items():
        for year, month in target_date:
            soup = fetch_group_schedule(url, headers, year, month)
            if not soup:
                logger.error(
                    "Failed fetch: group=%s year=%s month=%s",
                    group_name,
                    year,
                    month,
                )
                continue

            cells = soup.select(".calendarBody .cell")
            if not cells:
                logger.error(
                    "No cells found: group=%s year=%s month=%s",
                    group_name,
                    year,
                    month,
                )
                continue

            for cell in cells:
                events = parse_cell(cell, year, month, url)

                for event in events:
                    event_date = datetime.strptime(event["date"], "%Y-%m-%d").date()
                    if event_date < today:
                        continue
                    schedules_by_group[group_name].append(event)

        logger.debug(
            "Scraped %d events for %s",
            len(schedules_by_group[group_name]),
            group_name,
        )

    return schedules_by_group
