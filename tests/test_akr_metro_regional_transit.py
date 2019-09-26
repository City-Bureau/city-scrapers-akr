from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import BOARD, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.akr_metro_regional_transit import AkrMetroRegionalTransitSpider

test_response = file_response(
    join(dirname(__file__), "files", "akr_metro_regional_transit.html"),
    url="https://www.akronmetro.org/metro-board-meetings.aspx",
)
spider = AkrMetroRegionalTransitSpider()

freezer = freeze_time("2019-09-25")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]

freezer.stop()


def test_count():
    assert len(parsed_items) == 12


def test_title():
    assert parsed_items[0]["title"] == "Board of Trustees and Committees"


def test_description():
    assert parsed_items[0]["description"] == ""


def test_start():
    assert parsed_items[0]["start"] == datetime(2019, 1, 29, 8, 30)


def test_end():
    assert parsed_items[0]["end"] is None


def test_time_notes():
    assert parsed_items[0]["time_notes"] == ""


def test_id():
    assert parsed_items[0][
        "id"] == "akr_metro_regional_transit/201901290830/x/board_of_trustees_and_committees"


def test_status():
    assert parsed_items[0]["status"] == PASSED


def test_location():
    assert parsed_items[0]["location"] == spider.location


def test_source():
    assert parsed_items[0]["source"] == test_response.url


def test_links():
    assert parsed_items[0]["links"] == [{
        "href": "https://www.akronmetro.org/Data/Sites/2/pdf/january-2019-board-packet.pdf",
        "title": "Board Packet"
    }]


def test_classification():
    assert parsed_items[0]["classification"] == BOARD


def test_all_day():
    assert parsed_items[0]["all_day"] is False
