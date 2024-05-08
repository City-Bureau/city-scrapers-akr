from datetime import datetime
from os.path import dirname, join

import pytest
from city_scrapers_core.constants import BOARD, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.summ_library import SummLibrarySpider

test_response = file_response(
    join(dirname(__file__), "files", "summ_library.html"),
    url="https://www.akronlibrary.org/about/board-of-trustees/meetings",
)
spider = SummLibrarySpider()

freezer = freeze_time(datetime(2024, 5, 8, 14, 25))
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]
parsed_item = parsed_items[0]
freezer.stop()


def test_title():
    assert parsed_item["title"] == "Board of Trustees"


def test_description():
    assert parsed_item["description"] == ""


def test_start():
    assert parsed_item["start"] == datetime(2024, 1, 25, 16, 30)


def test_end():
    assert parsed_item["end"] is None


def test_time_notes():
    assert parsed_item["time_notes"] == ""


def test_id():
    assert parsed_item["id"] == "summ_library/202401251630/x/board_of_trustees"


def test_status():
    assert parsed_item["status"] == PASSED


def test_location():
    assert parsed_item["location"] == {
        "name": "Main Library",
        "address": "60 South High Street, Akron, OH 44326",
    }


def test_source():
    assert (
        parsed_item["source"]
        == "https://www.akronlibrary.org/about/board-of-trustees/meetings"
    )


def test_links():
    assert parsed_item["links"] == {
        "title": "Minutes page",
        "href": "https://www.akronlibrary.org/about/board-of-trustees/minutes",
    }


def test_classification():
    assert parsed_item["classification"] == BOARD


@pytest.mark.parametrize("item", parsed_items)
def test_all_day(item):
    assert item["all_day"] is False
