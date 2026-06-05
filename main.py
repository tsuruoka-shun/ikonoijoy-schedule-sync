import logging
import os

from dotenv import load_dotenv

from scraper.schedule import get_schedule
from sync.google_calendar import sync_events

load_dotenv()

logging_level = os.getenv("LOGGING_LEVEL")
logging.basicConfig(level=logging_level)
logger = logging.getLogger(__name__)
INFO_LOGGERS = [
    "urllib3",
    "googleapiclient.discovery",
]

ERROR_LOGGERS = [
    "google_auth_httplib2",
]

for name in INFO_LOGGERS:
    logging.getLogger(name).setLevel(logging.INFO)

for name in ERROR_LOGGERS:
    logging.getLogger(name).setLevel(logging.ERROR)


def main():
    logger.info("Scraping start")

    try:
        schedules_by_group = get_schedule()
    except Exception:
        logger.exception("Scraping failed, skipping sync")
        return

    logger.info("Scraping done\n")

    logger.info("Sync events start")

    sync_events(schedules_by_group)

    logger.info("Sync events done")


if __name__ == "__main__":
    main()
