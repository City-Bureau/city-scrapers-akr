from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import BOARD, TENTATIVE
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.summ_soil_water_conservation import SummSoilWaterConservationSpider

test_response = file_response(
    join(dirname(__file__), "files", "summ_soil_water_conservation.json"),
    url="https://clients6.google.com/calendar/v3/calendars/staffsummitswcd@gmail.com/events?",
)
spider = SummSoilWaterConservationSpider()

freezer = freeze_time("2019-10-03")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]

freezer.stop()


def test_count():
    assert len(parsed_items) == 1


def test_title():
    assert parsed_items[0]["title"] == "Summit SWCD Board"


def test_description():
    assert parsed_items[0]["description"] == ""


def test_start():
    assert parsed_items[0]["start"] == datetime(2019, 10, 22, 10, 0)


def test_end():
    assert parsed_items[0]["end"] == datetime(2019, 10, 22, 12, 0)


def test_time_notes():
    assert parsed_items[0]["time_notes"] == ""


def test_id():
    assert parsed_items[0]["id"] == "summ_soil_water_conservation/201910221000/x/summit_swcd_board"


def test_status():
    assert parsed_items[0]["status"] == TENTATIVE


def test_location():
    assert parsed_items[0]["location"] == {
        "name": "Coventry Oaks Pavilion - Firestone Metro Park",
        "address": "40 Axline Ave, Akron, OH 44319, USA"
    }


def test_source():
    assert parsed_items[0]["source"] == "https://sswcd.summitoh.net/about-us/calendar"


def test_links():
    assert parsed_items[0]["links"] == []


def test_classification():
    assert parsed_items[0]["classification"] == BOARD


def test_all_day():
    assert parsed_items[0]["all_day"] is False
