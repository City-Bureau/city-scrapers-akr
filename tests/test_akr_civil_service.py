from datetime import datetime
from os.path import dirname, join

import pytest
from city_scrapers_core.constants import COMMISSION, TENTATIVE
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.akr_civil_service import AkrCivilServiceSpider

test_response = file_response(
    join(dirname(__file__), "files", "akr_civil_service.html"),
    url="https://city-scrapers-notice-emails.s3.amazonaws.com/akr_civil_service/latest.eml",  # noqa
)
spider = AkrCivilServiceSpider()

freezer = freeze_time("2020-01-14")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]

freezer.stop()


def test_count():
    assert len(parsed_items) == 1


def test_title():
    assert parsed_items[0]["title"] == "Commission"


def test_description():
    assert parsed_items[0]["description"] == ""


def test_start():
    assert parsed_items[0]["start"] == datetime(2020, 1, 16, 13, 0)


def test_end():
    assert parsed_items[0]["end"] is None


def test_time_notes():
    assert parsed_items[0]["time_notes"] == "Confirm details with agency"


def test_id():
    assert parsed_items[0]["id"] == "akr_civil_service/202001161300/x/commission"


def test_status():
    assert parsed_items[0]["status"] == TENTATIVE


def test_location():
    assert parsed_items[0]["location"] == spider.location


def test_source():
    assert parsed_items[0]["source"] == test_response.url


def test_links():
    assert parsed_items[0]["links"] == []


def test_classification():
    assert parsed_items[0]["classification"] == COMMISSION


@pytest.mark.parametrize("item", parsed_items)
def test_all_day(item):
    assert item["all_day"] is False
