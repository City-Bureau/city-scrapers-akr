from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import ADVISORY_COMMITTEE, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.akr_metro_transportation_study import (
    AkrMetroTransportationStudySpider,
)

test_response = file_response(
    join(dirname(__file__), "files", "akr_metro_transportation_study_detail.html"),
    url="http://amatsplanning.org/calendars/technical-advisory-committee-9/",
)
test_docs_response = file_response(
    join(dirname(__file__), "files", "akr_metro_transportation_study.html"),
    url="http://amatsplanning.org/category/meetings/",
)
spider = AkrMetroTransportationStudySpider()

freezer = freeze_time("2019-09-30")
freezer.start()

spider.month_link_map = spider._parse_archive(test_docs_response)
parsed_item = [item for item in spider._parse_event(test_response)][0]

freezer.stop()


def test_title():
    assert parsed_item["title"] == "Technical Advisory Committee"


def test_description():
    assert parsed_item["description"] == ""


def test_start():
    assert parsed_item["start"] == datetime(2019, 5, 9, 13, 30)


def test_end():
    assert parsed_item["end"] == datetime(2019, 5, 9, 16, 0)


def test_time_notes():
    assert parsed_item["time_notes"] == ""


def test_id():
    assert (
        parsed_item["id"]
        == "akr_metro_transportation_study/201905091330/x/technical_advisory_committee"
    )


def test_status():
    assert parsed_item["status"] == PASSED


def test_location():
    assert parsed_item["location"] == {
        "name": "Hilton Garden Inn",
        "address": "1307 E. Market St. Akron OH 44305",
    }


def test_source():
    assert parsed_item["source"] == test_response.url


def test_links():
    assert parsed_item["links"] == [
        {
            "href": "http://amatsplanning.org/wp-content/uploads/TAC-CIC-and-Policy-Committee-Meeting-Materials-May-2019.pdf",  # noqa
            "title": "Meeting Packet",
        },
        {
            "title": "Technical Advisory Committee Podcast",
            "href": "http://amatsplanning.org/wp-content/uploads/TAC-5-9-19-1.mp3",
        },
    ]


def test_classification():
    assert parsed_item["classification"] == ADVISORY_COMMITTEE


def test_all_day():
    assert parsed_item["all_day"] is False
