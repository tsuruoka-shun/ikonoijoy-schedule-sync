import logging

from schedule_calendar.add_schedules import add_schedules
from scraper.get_schedules import get_schedules

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    logger.info("scraping start")

    schedules = get_schedules()

    logger.info("equal_love: %d件", len(schedules["equal_love"]))
    logger.info("not_equal_me: %d件", len(schedules["not_equal_me"]))
    logger.info("nearly_equal_joy: %d件", len(schedules["nearly_equal_joy"]))
    logger.info("scraping done")

    logger.info("add to schedules start")

    add_schedules(schedules)

    logger.info("add to schedules done")


if __name__ == "__main__":
    main()
