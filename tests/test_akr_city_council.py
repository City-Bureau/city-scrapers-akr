from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import CITY_COUNCIL, TENTATIVE
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.akr_city_council import AkrCityCouncilSpider

test_response = file_response(
    join(dirname(__file__), "files", "akr_city_council.html"),
    url="http://www.akroncitycouncil.org/upcoming-meetings/",
)
test_detail_response = file_response(
    join(dirname(__file__), "files", "akr_city_council_detail.html"),
    url=(
        "https://onlinedocs.akronohio.gov/OnBaseAgendaOnline/Documents/ViewAgenda?meetingId=262&doctype=1"  # noqa
    ),
)

EXPECTED_LINKS = [
    {
        "title": "Agenda",
        "href": "https://onlinedocs.akronohio.gov/OnBaseAgendaOnline/Documents/ViewDocument/November_25%2c_2019_271_Agenda_11_25_2019_7_00_00_PM.pdf?documentType=1&meetingId=271",  # noqa
    }
]

spider = AkrCityCouncilSpider()

freezer = freeze_time("2019-09-16")
freezer.start()

parsed_filter_items = [item for item in spider.parse(test_response)]
parsed_items = [
    item for item in spider._parse_detail(test_detail_response, links=EXPECTED_LINKS)
]

freezer.stop()


def test_count():
    assert len(parsed_filter_items) == 8
    assert len(parsed_items) == 1


def test_title():
    assert parsed_items[0]["title"] == "Regular council meeting"


def test_description():
    assert parsed_items[0]["description"] == ""


def test_start():
    assert parsed_items[0]["start"] == datetime(2019, 9, 16, 0, 0)


def test_end():
    assert parsed_items[0]["end"] is None


def test_time_notes():
    assert parsed_items[0]["time_notes"] == ""


def test_id():
    assert (
        parsed_items[0]["id"]
        == "akr_city_council/201909160000/x/regular_council_meeting"
    )


def test_status():
    assert parsed_items[0]["status"] == TENTATIVE


def test_location():
    assert parsed_items[0]["location"] == spider.location


def test_source():
    assert (
        parsed_items[0]["source"]
        == "https://onlinedocs.akronohio.gov/OnBaseAgendaOnline/Documents/ViewAgenda?meetingId=262&doctype=1"  # noqa
    )


def test_links():
    assert parsed_items[0]["links"] == EXPECTED_LINKS


def test_classification():
    assert parsed_items[0]["classification"] == CITY_COUNCIL


def test_all_day():
    assert parsed_items[0]["all_day"] is False
