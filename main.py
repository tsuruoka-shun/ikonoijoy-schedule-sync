import logging

from schedule_calendar.sync_schedules import sync_schedules
from scraper.get_schedules import get_schedules

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def main():
    logger.info("Scraping start")

    try:
        schedules = get_schedules()
    except Exception:
        logger.exception("Scraping failed, skipping sync")
        return

    logger.info("Scraping done\n")

    logger.info("Add to schedules start")

    sync_schedules(schedules)

    logger.info("Add to schedules done")


if __name__ == "__main__":
    main()
