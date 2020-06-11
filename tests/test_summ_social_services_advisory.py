from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import COMMITTEE, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.summ_social_services_advisory import (
    SummSocialServicesAdvisorySpider,
)

test_response = file_response(
    join(dirname(__file__), "files", "summ_social_services_advisory.eml"),
    url=(
        "https://city-scrapers-notice-emails.s3.amazonaws.com/summ_social_services_advisory/latest.eml"  # noqa
    ),
)
spider = SummSocialServicesAdvisorySpider()

freezer = freeze_time("2019-10-08")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]

freezer.stop()


def test_count():
    assert len(parsed_items) == 16


def test_title():
    assert parsed_items[0]["title"] == "Health and Human Services Committee"


def test_description():
    assert parsed_items[0]["description"] == ""


def test_start():
    assert parsed_items[0]["start"] == datetime(2019, 1, 17, 14, 0)


def test_end():
    assert parsed_items[0]["end"] == datetime(2019, 1, 17, 15, 30)


def test_time_notes():
    assert parsed_items[0]["time_notes"] == "Confirm details with agency"


def test_id():
    assert (
        parsed_items[0]["id"]
        == "summ_social_services_advisory/201901171400/x/health_and_human_services_committee"  # noqa
    )


def test_status():
    assert parsed_items[0]["status"] == PASSED


def test_location():
    assert parsed_items[0]["location"] == spider.location


def test_source():
    assert parsed_items[0]["source"] == test_response.url


def test_links():
    assert parsed_items[0]["links"] == []


def test_classification():
    assert parsed_items[0]["classification"] == COMMITTEE


def test_all_day():
    assert parsed_items[0]["all_day"] is False
