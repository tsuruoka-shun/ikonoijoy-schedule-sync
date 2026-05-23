import logging

from scraper.schedule import get_schedule
from sync.google_calendar import sync_events

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
for lib in [
    "urllib3",
    "googleapiclient.discovery",
    "google_auth_httplib2",
]:
    logging.getLogger(lib).setLevel(logging.INFO)


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
