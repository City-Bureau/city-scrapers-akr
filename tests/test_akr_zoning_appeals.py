from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import BOARD, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.akr_zoning_appeals import AkrZoningAppealsSpider

test_response = file_response(
    join(dirname(__file__), "files", "akr_zoning_appeals.pdf"),
    url="https://www.akronohio.gov/cms/site/462db8daed9dd330/index.html",
    mode="rb",
)
spider = AkrZoningAppealsSpider()

freezer = freeze_time("2019-09-27")
freezer.start()

parsed_items = [item for item in spider._parse_calendar(test_response)]

freezer.stop()


def test_count():
    assert len(parsed_items) == 12


def test_title():
    assert parsed_items[0]["title"] == "Board of Zoning Appeals"


def test_description():
    assert parsed_items[0]["description"] == ""


def test_start():
    assert parsed_items[0]["start"] == datetime(2019, 1, 30, 15, 0)


def test_end():
    assert parsed_items[0]["end"] is None


def test_time_notes():
    assert parsed_items[0]["time_notes"] == "Confirm details with agency"


def test_id():
    assert parsed_items[0]["id"] == "akr_zoning_appeals/201901301500/x/board_of_zoning_appeals"


def test_status():
    assert parsed_items[0]["status"] == PASSED


def test_location():
    assert parsed_items[0]["location"] == spider.location


def test_source():
    assert parsed_items[0]["source"] == spider.start_urls[0]


def test_links():
    assert parsed_items[0]["links"] == []


def test_classification():
    assert parsed_items[0]["classification"] == BOARD


def test_all_day():
    assert parsed_items[0]["all_day"] is False
