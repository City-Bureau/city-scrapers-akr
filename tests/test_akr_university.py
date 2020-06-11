from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import BOARD, COMMITTEE, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.akr_university import AkrUniversitySpider

test_response = file_response(
    join(dirname(__file__), "files", "akr_university.html"),
    url="https://www.uakron.edu/bot/meetings.dot",
)
test_docs_response = file_response(
    join(dirname(__file__), "files", "akr_university_docs.html"),
    url="https://www.uakron.edu/bot/board-memos.dot?folderPath=/bot/docs/2019",
)
spider = AkrUniversitySpider()

freezer = freeze_time("2019-09-30")
freezer.start()

spider.link_date_map = spider._parse_docs(test_docs_response)
parsed_items = [item for item in spider._parse_schedule(test_response)]

freezer.stop()


def test_count():
    assert len(parsed_items) == 10


def test_title():
    assert parsed_items[0]["title"] == "Board of Trustees"


def test_description():
    assert parsed_items[0]["description"] == ""


def test_start():
    assert parsed_items[0]["start"] == datetime(2019, 8, 14, 10, 30)


def test_end():
    assert parsed_items[0]["end"] is None


def test_time_notes():
    assert parsed_items[0]["time_notes"] == ""


def test_id():
    assert parsed_items[0]["id"] == "akr_university/201908141030/x/board_of_trustees"


def test_status():
    assert parsed_items[0]["status"] == PASSED


def test_location():
    assert parsed_items[0]["location"] == spider.location


def test_source():
    assert parsed_items[0]["source"] == test_response.url


def test_links():
    assert parsed_items[0]["links"] == [
        {
            "href": "https://www.uakron.edu/bot/docs/2019/Board book for August 14 2019 updated 09042019.pdf",  # noqa
            "title": "Materials",
        },
        {"title": "Livestream", "href": "https://learn.uakron.edu/video/bot/"},
    ]


def test_classification():
    assert parsed_items[0]["classification"] == BOARD
    assert parsed_items[-1]["classification"] == COMMITTEE


def test_all_day():
    assert parsed_items[0]["all_day"] is False
