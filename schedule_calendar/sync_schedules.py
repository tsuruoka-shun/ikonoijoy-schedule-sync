import calendar
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build

load_dotenv()

logger = logging.getLogger(__name__)
logging.getLogger("urllib3.connectionpool").setLevel(logging.INFO)
logging.getLogger("googleapiclient.discovery").setLevel(logging.INFO)
logging.getLogger("google_auth_httplib2").setLevel(logging.INFO)

JST = ZoneInfo("Asia/Tokyo")
today = datetime.now(JST)
_, last_day = calendar.monthrange(today.year, today.month)
one_week_ago = today - timedelta(days=7)
one_week_ago_midnight = one_week_ago.replace(hour=0, minute=0, second=0, tzinfo=JST)
month_last = datetime(today.year, today.month, last_day, 23, 59, 59, tzinfo=JST)


credentials = service_account.Credentials.from_service_account_file(
    Path(__file__).resolve().parent.parent / "credentials/service_account.json",
    scopes=["https://www.googleapis.com/auth/calendar"],
)
service = build("calendar", "v3", credentials=credentials)

CALENDAR_ID = {
    "equal_love": os.getenv("EQUAL_LOVE_CALENDAR_ID"),
    "not_equal_me": os.getenv("NOT_EQUAL_ME_CALENDAR_ID"),
    "nearly_equal_joy": os.getenv("NEARLY_EQUAL_JOY_CALENDAR_ID"),
}


def sync_schedules(schedules: dict[str, list[dict[str, str]]]) -> None:
    for group_name, group_schedules in schedules.items():
        logger.info("Processing group: %s", group_name)
        added_count = 0
        duplicate_count = 0

        existing_links = set()
        page_token = None
        while True:
            events = (
                service.events()
                .list(
                    calendarId=CALENDAR_ID[group_name],
                    timeMin=one_week_ago_midnight.isoformat(),
                    timeMax=month_last.isoformat(),
                    timeZone="Asia/Tokyo",
                    singleEvents=True,
                    maxResults=100,
                    fields="items(summary,start,end,extendedProperties(private/source_link)),nextPageToken",
                    pageToken=page_token,
                )
                .execute()
            )
            for e in events.get("items", []):
                link = (
                    e.get("extendedProperties", {})
                    .get("private", {})
                    .get("source_link")
                )
                if link:
                    existing_links.add(link)

            page_token = events.get("nextPageToken")
            if not page_token:
                break

        logger.info(
            "Fetched %d existing events from Google Calendar (group: %s)",
            len(existing_links),
            group_name,
        )

        for schedule in group_schedules:
            if schedule["link"] in existing_links:
                duplicate_count += 1
                continue
            next_day = datetime.strptime(
                schedule["date"], "%Y-%m-%d"
            ).date() + timedelta(days=1)
            event = {
                "summary": schedule["title"],
                "start": {
                    "date": schedule["date"],
                },
                "end": {"date": next_day.strftime("%Y-%m-%d")},
                "description": schedule["link"],
                "extendedProperties": {"private": {"source_link": schedule["link"]}},
            }
            try:
                service.events().insert(
                    calendarId=CALENDAR_ID[group_name], body=event
                ).execute()
                logger.debug(
                    "Added event to %s '%s'", schedule["date"], schedule["title"]
                )
                added_count += 1
            except Exception as e:
                logger.error("Failed to add event '%s': %s", schedule["title"], e)
        logger.info(
            "Skipped %d duplicate events (group: %s)",
            duplicate_count,
            group_name,
        )
        logger.info(
            "Added %d new events (group: %s)\n",
            added_count,
            group_name,
        )
    return None
