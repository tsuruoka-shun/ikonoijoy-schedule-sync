import logging

from schedule_calendar.add_schedules import add_schedules
from scraper.get_schedules import get_schedules

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    logger.info("Scraping start")

    schedules = get_schedules()

    logger.info("Scraping done\n")

    logger.info("Add to schedules start\n")

    add_schedules(schedules)

    logger.info("Add to schedules done")


if __name__ == "__main__":
    main()
