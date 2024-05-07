from datetime import datetime
from os.path import dirname, join

import pytest
from city_scrapers_core.constants import BOARD, TENTATIVE
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.summ_alcohol_drug_mental_health import (
    SummAlcoholDrugMentalHealthSpider,
)

test_response = file_response(
    join(dirname(__file__), "files", "summ_alcohol_drug_mental_health.html"),
    url="https://admboard.org/board-of-directors/",
)
spider = SummAlcoholDrugMentalHealthSpider()

freezer = freeze_time(datetime(2024, 5, 7, 13, 59))
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]
parsed_item = parsed_items[0]
freezer.stop()


def test_title():
    assert parsed_item["title"] == "ADM Board of Directors Meeting (MAY 28)"


def test_description():
    assert (
        parsed_item["description"]
        == "Summit County Public Health Board Room, 1867 W. Market St., Entrance A, Akron, OH click here for map "  # noqa
    )


def test_start():
    assert parsed_item["start"] == datetime(2024, 5, 28, 16, 30)


def test_end():
    assert parsed_item["end"] == datetime(2024, 5, 28, 18, 0)


def test_time_notes():
    assert parsed_item["time_notes"] == ""


def test_id():
    assert (
        parsed_item["id"]
        == "summ_alcohol_drug_mental_health/202405281630/x/adm_board_of_directors_meeting_may_28_"  # noqa
    )


def test_status():
    assert parsed_item["status"] == TENTATIVE


def test_location():
    assert parsed_item["location"] == {
        "name": "Summit County Public Health Board Room",
        "address": "1867 West Market Street, Entrance A",
    }


def test_source():
    assert (
        parsed_item["source"]
        == "https://admboard.org/events/may-28-adm-board-of-directors-meeting/"
    )


def test_links():
    assert parsed_item["links"] == [
        {
            "title": "Event Details",
            "href": "https://admboard.org/events/may-28-adm-board-of-directors-meeting/",  # noqa
        }
    ]


def test_classification():
    assert parsed_item["classification"] == BOARD


@pytest.mark.parametrize("item", parsed_items)
def test_all_day(item):
    assert item["all_day"] is False
