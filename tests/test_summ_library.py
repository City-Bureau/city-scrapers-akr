from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import BOARD, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.summ_library import SummLibrarySpider

test_response = file_response(
    join(dirname(__file__), "files", "summ_library.html"),
    url="https://www.akronlibrary.org/about/board-of-trustees/meetings",
)
test_minutes_response = file_response(
    join(dirname(__file__), "files", "summ_library_minutes.html"),
    url="https://www.akronlibrary.org/about/board-of-trustees/minutes",
)
spider = SummLibrarySpider()

freezer = freeze_time("2019-09-26")
freezer.start()

spider.minutes_map = spider._parse_minutes(test_minutes_response)
parsed_items = [item for item in spider._parse_meetings(test_response)]

freezer.stop()


def test_count():
    assert len(parsed_items) == 11


def test_title():
    assert parsed_items[0]["title"] == "Board of Trustees"


def test_description():
    assert parsed_items[0]["description"] == ""


def test_start():
    assert parsed_items[0]["start"] == datetime(2019, 1, 31, 16, 0)


def test_end():
    assert parsed_items[0]["end"] is None


def test_time_notes():
    assert parsed_items[0]["time_notes"] == ""


def test_id():
    assert parsed_items[0]["id"] == "summ_library/201901311600/x/board_of_trustees"


def test_status():
    assert parsed_items[0]["status"] == PASSED


def test_location():
    assert parsed_items[0]["location"] == {
        "name": "Main Library",
        "address": "60 South High Street, Akron, OH 44326",
    }


def test_source():
    assert parsed_items[0]["source"] == test_response.url


def test_links():
    assert parsed_items[0]["links"] == [{
        "href": "https://www.akronlibrary.org/images/boardMinutes/2019/1_2019_Board_Minutes.pdf",
        "title": "Board Minutes"
    }]


def test_classification():
    assert parsed_items[0]["classification"] == BOARD


def test_all_day():
    assert parsed_items[0]["all_day"] is False
