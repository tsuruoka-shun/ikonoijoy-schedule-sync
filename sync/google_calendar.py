import calendar
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Protocol, TypedDict
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build

load_dotenv()

logger = logging.getLogger(__name__)

cred = service_account.Credentials.from_service_account_file(
    Path(__file__).resolve().parent.parent / "credentials/service_account.json",
    scopes=["https://www.googleapis.com/auth/calendar"],
)
service = build("calendar", "v3", credentials=cred)

CALENDAR_IDS = {
    "equal_love": os.environ["EQUAL_LOVE_CALENDAR_ID"],
    "not_equal_me": os.environ["NOT_EQUAL_ME_CALENDAR_ID"],
    "nearly_equal_joy": os.environ["NEARLY_EQUAL_JOY_CALENDAR_ID"],
}


class ScrapEvent(TypedDict):
    date: str
    title: str
    link: str


class SourceLink(TypedDict):
    source_link: str


class ExtendedProperties(TypedDict):
    private: SourceLink


class GoogleEventDate(TypedDict):
    date: str


class GoogleEvent(TypedDict):
    id: str
    summary: str
    start: GoogleEventDate
    end: GoogleEventDate
    extendedProperties: ExtendedProperties


class EventBody(TypedDict):
    summary: str
    start: GoogleEventDate
    end: GoogleEventDate
    description: str
    extendedProperties: ExtendedProperties


class GoogleRequest(Protocol):
    def execute(self) -> dict: ...


def get_time_bounds(time_zone: str = "Asia/Tokyo") -> tuple[datetime, datetime]:
    tz = ZoneInfo(time_zone)
    today = datetime.now(tz)
    _, last_day = calendar.monthrange(today.year, today.month)
    fetch_since = today.replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )
    fetch_until = today.replace(
        day=last_day,
        hour=23,
        minute=59,
        second=59,
        microsecond=59,
    )
    return (
        fetch_since,
        fetch_until,
    )


def fetch_google_calendar_events(
    calendar_id: str,
    time_min: datetime,
    time_max: datetime,
) -> dict[str, GoogleEvent]:
    google_calendar_events: dict[str, GoogleEvent] = {}
    page_token: str | None = None

    while True:
        events = (
            service.events()
            .list(
                calendarId=calendar_id,
                timeMin=time_min.isoformat(),
                timeMax=time_max.isoformat(),
                timeZone="Asia/Tokyo",
                singleEvents=True,
                maxResults=100,
                fields="items(id, summary, start, end, extendedProperties(private/source_link)), nextPageToken",
                pageToken=page_token,
            )
            .execute()
        )
        for event in events.get("items", []):
            link = (
                event.get("extendedProperties", {})
                .get("private", {})
                .get("source_link")
            )
            if link:
                google_calendar_events[link] = event

        page_token = events.get("nextPageToken")
        if not page_token:
            break
    logger.debug("Fetched %d existing events", len(google_calendar_events))
    return google_calendar_events


def build_calendar_event_body(
    title: str,
    date: str,
    link: str,
) -> EventBody:
    next_day = datetime.strptime(date, "%Y-%m-%d").date() + timedelta(days=1)
    return {
        "summary": title,
        "start": {"date": date},
        "end": {"date": next_day.strftime("%Y-%m-%d")},
        "description": link,
        "extendedProperties": {"private": {"source_link": link}},
    }


def execute_calendar_request(
    request: GoogleRequest,
    success_msg: str,
    error_msg: str,
    *log_args,
) -> bool:
    try:
        request.execute()
        logger.debug(success_msg, *log_args)
        return True
    except Exception:
        logger.exception(error_msg, *log_args)
        return False


def create_calendar_event(
    calendar_id: str,
    event_body: EventBody,
) -> bool:
    return execute_calendar_request(
        service.events().insert(
            calendarId=calendar_id,
            body=event_body,
        ),
        "Created event '%s' on %s",
        "Failed to create event '%s': %s",
        event_body["summary"],
        event_body["start"]["date"],
    )


def update_calendar_event(
    calendar_id: str,
    event_id: str,
    event_body: EventBody,
) -> bool:
    return execute_calendar_request(
        service.events().update(
            calendarId=calendar_id,
            eventId=event_id,
            body=event_body,
        ),
        "Updated event '%s' on %s",
        "Failed to update event '%s': %s",
        event_body["summary"],
        event_body["start"]["date"],
    )


def delete_calendar_event(
    calendar_id: str,
    event_id: str,
    summary: str,
    date: str,
) -> bool:
    return execute_calendar_request(
        service.events().delete(
            calendarId=calendar_id,
            eventId=event_id,
        ),
        "Deleted event '%s' on %s",
        "Failed to delete event '%s': %s",
        summary,
        date,
    )


def sync_group_events(
    group_name: str,
    scraped_events: list[ScrapEvent],
    time_min: datetime,
    time_max: datetime,
) -> None:
    logger.info("Processing group: %s", group_name)
    create_count = update_count = delete_count = skip_count = 0
    calendar_id = CALENDAR_IDS[group_name]

    google_calendar_events = fetch_google_calendar_events(
        calendar_id,
        time_min,
        time_max,
    )

    for scraped_event in scraped_events:
        google_calendar_event = google_calendar_events.get(scraped_event["link"])
        event_body = build_calendar_event_body(
            scraped_event["title"],
            scraped_event["date"],
            scraped_event["link"],
        )

        if not google_calendar_event:
            if create_calendar_event(
                calendar_id,
                event_body,
            ):
                create_count += 1
            continue

        is_changed = (
            google_calendar_event["summary"] != scraped_event["title"]
            or google_calendar_event["start"]["date"] != scraped_event["date"]
        )
        if is_changed:
            if update_calendar_event(
                calendar_id,
                google_calendar_event["id"],
                event_body,
            ):
                update_count += 1
        else:
            skip_count += 1

    scraped_event_links = {scraped_event["link"] for scraped_event in scraped_events}
    for link, google_calendar_event in google_calendar_events.items():
        if link not in scraped_event_links:
            if delete_calendar_event(
                calendar_id,
                google_calendar_event["id"],
                google_calendar_event["summary"],
                google_calendar_event["start"]["date"],
            ):
                delete_count += 1
    logger.info(
        "Sync completed: created=%d, updated=%d, deleted=%d, skipped=%d",
        create_count,
        update_count,
        delete_count,
        skip_count,
    )


def sync_events(schedules_by_group: dict[str, list[ScrapEvent]]) -> None:
    time_min, time_max = get_time_bounds()

    for group_name, scraped_events in schedules_by_group.items():
        sync_group_events(
            group_name,
            scraped_events,
            time_min,
            time_max,
        )
