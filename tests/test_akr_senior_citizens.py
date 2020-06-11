from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import COMMISSION, TENTATIVE
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.akr_senior_citizens import AkrSeniorCitizensSpider

test_response = file_response(
    join(dirname(__file__), "files", "akr_senior_citizens.eml"),
    url="https://city-scrapers-notice-emails.s3.amazonaws.com/akr_senior_citizens/latest.eml",  # noqa
)
spider = AkrSeniorCitizensSpider()

freezer = freeze_time("2019-10-31")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]

freezer.stop()


def test_count():
    assert len(parsed_items) == 1


def test_title():
    assert parsed_items[0]["title"] == "Senior Citizens Commission"


def test_description():
    assert parsed_items[0]["description"] == ""


def test_start():
    assert parsed_items[0]["start"] == datetime(2019, 11, 18, 12, 0)


def test_end():
    assert parsed_items[0]["end"] == datetime(2019, 11, 18, 13, 30)


def test_time_notes():
    assert parsed_items[0]["time_notes"] == ""


def test_id():
    assert (
        parsed_items[0]["id"]
        == "akr_senior_citizens/201911181200/x/senior_citizens_commission"
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
    assert parsed_items[0]["classification"] == COMMISSION


def test_all_day():
    assert parsed_items[0]["all_day"] is False
