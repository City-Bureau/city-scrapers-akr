from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import FORUM, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.akr_downtown_partnership import AkrDowntownPartnershipSpider

test_response = file_response(
    join(dirname(__file__), "files", "akr_downtown_partnership.html"),
    url="https://www.downtownakron.com/work/district-meetings",
)
spider = AkrDowntownPartnershipSpider()

freezer = freeze_time("2019-10-02")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]

freezer.stop()


def test_count():
    assert len(parsed_items) == 10


def test_title():
    assert parsed_items[0]["title"] == "Northside District"


def test_description():
    assert parsed_items[0]["description"] == ""


def test_start():
    assert parsed_items[0]["start"] == datetime(2019, 9, 12, 13, 30)


def test_end():
    assert parsed_items[0]["end"] is None


def test_time_notes():
    assert parsed_items[0]["time_notes"] == "See source to confirm details"


def test_id():
    assert parsed_items[0]["id"] == "akr_downtown_partnership/201909121330/x/northside_district"


def test_status():
    assert parsed_items[0]["status"] == PASSED


def test_location():
    assert parsed_items[0]["location"] == {
        "name": "Jilly's Music Room",
        "address": "111 N Main St, Akron, OH 44308",
    }


def test_source():
    assert parsed_items[0]["source"] == test_response.url


def test_links():
    assert parsed_items[0]["links"] == []


def test_classification():
    assert parsed_items[0]["classification"] == FORUM


def test_all_day():
    assert parsed_items[0]["all_day"] is False
