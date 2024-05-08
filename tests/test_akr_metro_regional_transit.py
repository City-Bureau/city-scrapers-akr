from datetime import datetime
from os.path import dirname, join

import pytest
from city_scrapers_core.constants import BOARD, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.akr_metro_regional_transit import (
    AkrMetroRegionalTransitSpider,
)

test_response = file_response(
    join(dirname(__file__), "files", "akr_metro_regional_transit.html"),
    url="https://www.akronmetro.org/metro-board-meetings.aspx",
)
spider = AkrMetroRegionalTransitSpider()

freezer = freeze_time(datetime(2024, 5, 8, 14, 4))
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]
parsed_item = parsed_items[0]
freezer.stop()


def test_title():
    assert parsed_item["title"] == "Board meeting"


def test_description():
    assert parsed_item["description"] == ""


def test_start():
    assert parsed_item["start"] == datetime(2024, 1, 30, 9, 0)


def test_end():
    assert parsed_item["end"] is None


def test_time_notes():
    assert parsed_item["time_notes"] == ""


def test_id():
    assert (
        parsed_item["id"] == "akr_metro_regional_transit/202401300900/x/board_meeting"
    )


def test_status():
    assert parsed_item["status"] == PASSED


def test_location():
    assert parsed_item["location"] == {
        "name": "Robert K. Pfaff Transit Center",
        "address": "631 S Broadway St, Akron, OH 44311",
    }


def test_source():
    assert (
        parsed_item["source"] == "https://www.akronmetro.org/metro-board-meetings.aspx"
    )


def test_links():
    assert parsed_item["links"] == [
        {"title": "Board Packet", "href": "/Data/Sites/2/board-packet-1.30.24.pdf"},
        {"title": "Minutes", "href": "/Data/Sites/2/board-minutes-1.30.24-signed.pdf"},
    ]


def test_classification():
    assert parsed_item["classification"] == BOARD


@pytest.mark.parametrize("item", parsed_items)
def test_all_day(item):
    assert item["all_day"] is False
