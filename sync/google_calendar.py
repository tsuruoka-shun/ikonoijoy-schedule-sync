import calendar
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Protocol, TypedDict
from zoneinfo import ZoneInfo

from dateutil.relativedelta import relativedelta
from google.auth import default
from google.cloud import secretmanager_v1
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

client = secretmanager_v1.SecretManagerServiceClient()

PROJECT_ID = os.environ["PROJECT_ID"]
SECRET_NAME = os.environ["CALENDAR_SECRET_NAME"]


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


def get_calendar_ids() -> dict[str, str]:
    name = f"projects/{PROJECT_ID}/secrets/{SECRET_NAME}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return json.loads(response.payload.data.decode("UTF-8"))


def get_calendar_service():
    cred, _ = default(scopes=["https://www.googleapis.com/auth/calendar"])
    return build(
        "calendar",
        "v3",
        credentials=cred,
        cache_discovery=False,
    )


def get_time_bounds(time_zone: str = "Asia/Tokyo") -> tuple[datetime, datetime]:
    tz = ZoneInfo(time_zone)
    today = datetime.now(tz)
    next_month_date = today + relativedelta(months=1)
    _, last_day = calendar.monthrange(next_month_date.year, next_month_date.month)
    fetch_since = today.replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )
    fetch_until = next_month_date.replace(
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
    service,
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
    logger.debug(
        "Fetched %d existing events from google calendar", len(google_calendar_events)
    )
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
    service,
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
    service,
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
    service,
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
    service,
    calendar_ids: dict[str, str],
    time_min: datetime,
    time_max: datetime,
) -> None:
    logger.info("Processing group: %s", group_name)
    create_count = update_count = delete_count = skip_count = 0
    calendar_id = calendar_ids[group_name]

    google_calendar_events = fetch_google_calendar_events(
        service,
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
                service,
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
                service,
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
                service,
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
    service = get_calendar_service()
    calendar_ids = get_calendar_ids()
    time_min, time_max = get_time_bounds()

    for group_name, scraped_events in schedules_by_group.items():
        if not scraped_events:
            logger.error("Skipped sync events for %s", group_name)
            continue
        sync_group_events(
            group_name,
            scraped_events,
            service,
            calendar_ids,
            time_min,
            time_max,
        )
