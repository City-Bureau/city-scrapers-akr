from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import COMMITTEE, TENTATIVE
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.akr_city_council_committees import (
    AkrCityCouncilCommitteesSpider,
)

test_response = file_response(
    join(dirname(__file__), "files", "akr_city_council_committees.html"),
    url="https://onlinedocs.akronohio.gov/OnBaseAgendaOnline/Documents/ViewAgenda",  # noqa
)
test_detail_response = file_response(
    join(dirname(__file__), "files", "akr_city_council_committees_detail.html"),  # noqa
    url="https://onlinedocs.akronohio.gov/OnBaseAgendaOnline/Documents/ViewAgenda?meetingId=587&doctype=1",  # noqa
)

EXPECTED_LINKS = [
    {
        "title": "Agenda",
        "href": "https://onlinedocs.akronohio.gov/OnBaseAgendaOnline/Documents/ViewDocument/May_20%2c_2024_587_Agenda_5_20_2024_1_00_00_PM.pdf?documentType=1&meetingId=587",  # noqa
    }
]

spider = AkrCityCouncilCommitteesSpider()

freezer = freeze_time("2024-05-20")
freezer.start()

parsed_filter_items = [item for item in spider.parse(test_response)]
parsed_items = [
    item
    for item in spider._parse_detail(test_detail_response, links=EXPECTED_LINKS)  # noqa
]

freezer.stop()


def test_count():
    assert len(parsed_filter_items) == 5  # Adjusted based on data provided
    assert len(parsed_items) == 1


def test_title():
    assert parsed_items[0]["title"] == "Committee meeting"


def test_description():
    assert parsed_items[0]["description"].startswith(
        "Planning & Economic Development – 13:00:00"
    )


def test_start():
    assert parsed_items[0]["start"] == datetime(2024, 5, 20, 13, 0)


def test_end():
    assert parsed_items[0]["end"] == datetime(2024, 5, 20, 17, 0)


def test_time_notes():
    assert parsed_items[0]["time_notes"] == ""


def test_id():
    assert (
        parsed_items[0]["id"]
        == "akr_city_council_committees/202405201300/x/committee_meeting"  # noqa
    )


def test_status():
    assert parsed_items[0]["status"] == TENTATIVE


def test_location():
    assert parsed_items[0]["location"] == spider.location


def test_source():
    assert (
        parsed_items[0]["source"]
        == "https://onlinedocs.akronohio.gov/OnBaseAgendaOnline/Documents/ViewAgenda?meetingId=587&doctype=1"  # noqa
    )


def test_links():
    assert parsed_items[0]["links"] == EXPECTED_LINKS


def test_classification():
    assert parsed_items[0]["classification"] == COMMITTEE


def test_all_day():
    assert parsed_items[0]["all_day"] is False
