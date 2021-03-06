from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import BOARD, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.akr_public_schools import AkrPublicSchoolsSpider

test_response = file_response(
    join(dirname(__file__), "files", "akr_public_schools.xml"),
    url="https://go.boarddocs.com/oh/akron/Board.nsf/XML-ActiveMeetings",
)
spider = AkrPublicSchoolsSpider()

freezer = freeze_time("2019-09-27")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]

freezer.stop()


def test_count():
    assert len(parsed_items) == 7


def test_title():
    assert parsed_items[0]["title"] == "Board of Education"


def test_description():
    assert parsed_items[0]["description"] == ""


def test_start():
    assert parsed_items[0]["start"] == datetime(2019, 10, 7, 17, 30)


def test_end():
    assert parsed_items[0]["end"] is None


def test_time_notes():
    assert parsed_items[0]["time_notes"] == ""


def test_id():
    assert (
        parsed_items[0]["id"] == "akr_public_schools/201910071730/x/board_of_education"
    )


def test_status():
    assert parsed_items[1]["status"] == PASSED


def test_location():
    assert parsed_items[0]["location"] == spider.location


def test_source():
    assert (
        parsed_items[0]["source"]
        == "https://go.boarddocs.com/oh/akron/Board.nsf/Public"
    )
    assert (
        parsed_items[1]["source"]
        == "http://go.boarddocs.com/oh/akron/Board.nsf/goto?open&amp;id=BFPP3S6262FE"
    )


def test_links():
    assert parsed_items[0]["links"] == []
    assert parsed_items[1]["links"] == [
        {
            "href": "http://go.boarddocs.com/oh/akron/Board.nsf/goto?open&amp;id=BFPP3S6262FE",  # noqa
            "title": "Agenda",
        }
    ]


def test_classification():
    assert parsed_items[0]["classification"] == BOARD


def test_all_day():
    assert parsed_items[0]["all_day"] is False
