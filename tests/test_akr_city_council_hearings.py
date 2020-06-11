from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import FORUM, TENTATIVE
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.akr_city_council_hearings import AkrCityCouncilHearingsSpider

test_response = file_response(
    join(dirname(__file__), "files", "akr_city_council_hearings.html"),
    url="http://www.akroncitycouncil.org/upcoming-meetings/",
)
spider = AkrCityCouncilHearingsSpider()

freezer = freeze_time("2019-10-07")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]

freezer.stop()


def test_count():
    assert len(parsed_items) == 33


def test_title():
    assert parsed_items[1]["title"] == "Public Hearings"


def test_description():
    assert parsed_items[1]["description"] == "Conditional Use and Rezoning Requests"


def test_start():
    assert parsed_items[1]["start"] == datetime(2019, 10, 7, 19, 0)


def test_end():
    assert parsed_items[1]["end"] == datetime(2019, 10, 7, 20, 30)


def test_time_notes():
    assert parsed_items[1]["time_notes"] == ""


def test_id():
    assert (
        parsed_items[1]["id"]
        == "akr_city_council_hearings/201910071900/x/public_hearings"
    )


def test_status():
    assert parsed_items[1]["status"] == TENTATIVE


def test_location():
    assert parsed_items[1]["location"] == spider.location


def test_source():
    assert (
        parsed_items[1]["source"]
        == "http://www.akroncitycouncil.org/upcoming-meetings/public-hearings-1/"
    )


def test_links():
    assert parsed_items[1]["links"] == []


def test_classification():
    assert parsed_items[1]["classification"] == FORUM


def test_all_day():
    assert parsed_items[1]["all_day"] is False
