from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import COMMISSION, TENTATIVE
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.summ_veterans import SummVeteransSpider

test_response = file_response(
    join(dirname(__file__), "files", "summ_veterans.json"),
    url="https://clients6.google.com/calendar/v3/calendars/vscsummitcalendar@gmail.com/events"
)
spider = SummVeteransSpider()

freezer = freeze_time("2019-10-03")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]

freezer.stop()


def test_count():
    assert len(parsed_items) == 2


def test_title():
    assert parsed_items[0]["title"] == "Board of Commissioners"


def test_description():
    assert parsed_items[0]["description"] == ""


def test_start():
    assert parsed_items[0]["start"] == datetime(2019, 10, 9, 13, 0)


def test_end():
    assert parsed_items[0]["end"] == datetime(2019, 10, 9, 16, 0)


def test_time_notes():
    assert parsed_items[0]["time_notes"] == ""


def test_id():
    assert parsed_items[0]["id"] == "summ_veterans/201910091300/x/board_of_commissioners"


def test_status():
    assert parsed_items[0]["status"] == TENTATIVE


def test_location():
    assert parsed_items[0]["location"] == {
        "name": "",
        "address": "1060 E Waterloo Rd, Akron, OH 44306, USA",
    }


def test_source():
    assert parsed_items[0]["source"] == "http://www.vscsummitoh.us/calendar-of-events/"


def test_links():
    assert parsed_items[0]["links"] == []


def test_classification():
    assert parsed_items[0]["classification"] == COMMISSION


def test_all_day():
    assert parsed_items[0]["all_day"] is False
