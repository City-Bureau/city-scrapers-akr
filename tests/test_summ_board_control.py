from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import BOARD, TENTATIVE
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.summ_board_control import SummBoardControlSpider

test_response = file_response(
    join(dirname(__file__), "files", "summ_board_control.html"),
    url="https://co.summitoh.net/index.php/offices/boards-agencies-a-commissions/board-of-control",  # noqa
)
spider = SummBoardControlSpider()

freezer = freeze_time("2019-10-02")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]

freezer.stop()


def test_count():
    assert len(parsed_items) == 20


def test_title():
    assert parsed_items[0]["title"] == "Board of Control"


def test_description():
    assert parsed_items[0]["description"] == ""


def test_start():
    assert parsed_items[0]["start"] == datetime(2019, 10, 2, 10, 30)


def test_end():
    assert parsed_items[0]["end"] is None


def test_time_notes():
    assert parsed_items[0]["time_notes"] == "See agenda to confirm details"


def test_id():
    assert parsed_items[0]["id"] == "summ_board_control/201910021030/x/board_of_control"


def test_status():
    assert parsed_items[0]["status"] == TENTATIVE


def test_location():
    assert parsed_items[0]["location"] == spider.location


def test_source():
    assert parsed_items[0]["source"] == test_response.url


def test_links():
    assert parsed_items[0]["links"] == [
        {
            "href": "https://co.summitoh.net/images/stories/Finance/BOC/Agenda/19Agenda/10-02-19BOCAGENDA.pdf",  # noqa
            "title": "Agenda",
        }
    ]


def test_classification():
    assert parsed_items[0]["classification"] == BOARD


def test_all_day():
    assert parsed_items[0]["all_day"] is False
