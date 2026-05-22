import logging

from sync.google_calendar import sync_events
from scraper.schedule import get_schedule

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def main():
    logger.info("Scraping start")

    try:
        schedules = get_schedule()
    except Exception:
        logger.exception("Scraping failed, skipping sync")
        return

    logger.info("Scraping done\n")

    logger.info("Add to schedules start")

    sync_events(schedules)

    logger.info("Add to schedules done")


if __name__ == "__main__":
    main()
