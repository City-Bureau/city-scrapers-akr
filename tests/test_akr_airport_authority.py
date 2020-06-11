from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import BOARD, TENTATIVE
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.akr_airport_authority import AkrAirportAuthoritySpider

test_response = file_response(
    join(dirname(__file__), "files", "akr_airport_authority.eml"),
    url="https://city-scrapers-notice-emails.s3.amazonaws.com/akr_airport_authority/latest.eml",  # noqa
)
spider = AkrAirportAuthoritySpider()

freezer = freeze_time("2019-10-03")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]

freezer.stop()


def test_count():
    assert len(parsed_items) == 3


def test_title():
    assert parsed_items[0]["title"] == "Board of Trustees"


def test_description():
    assert parsed_items[0]["description"] == ""


def test_start():
    assert parsed_items[0]["start"] == datetime(2019, 10, 17, 15, 0)


def test_end():
    assert parsed_items[0]["end"] is None


def test_time_notes():
    assert parsed_items[0]["time_notes"] == "Confirm meeting details with agency"


def test_id():
    assert (
        parsed_items[0]["id"]
        == "akr_airport_authority/201910171500/x/board_of_trustees"
    )


def test_status():
    assert parsed_items[0]["status"] == TENTATIVE


def test_location():
    assert parsed_items[0]["location"] == spider.location


def test_source():
    assert parsed_items[0]["source"] == test_response.url


def test_links():
    assert parsed_items[0]["links"] == []


def test_classification():
    assert parsed_items[0]["classification"] == BOARD


def test_all_day():
    assert parsed_items[0]["all_day"] is False
