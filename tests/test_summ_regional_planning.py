from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import BOARD, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.summ_regional_planning import SummRegionalPlanningSpider

test_response = file_response(
    join(dirname(__file__), "files", "summ_regional_planning.html"),
    url="http://www.nefcoplanning.org/meetings.html",
)
spider = SummRegionalPlanningSpider()

freezer = freeze_time("2019-10-14")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]

freezer.stop()


def test_count():
    assert len(parsed_items) == 24


def test_title():
    assert parsed_items[0]["title"] == "NEFCO General Policy Board"


def test_description():
    assert parsed_items[0]["description"] == ""


def test_start():
    assert parsed_items[0]["start"] == datetime(2019, 1, 16, 8, 30)


def test_end():
    assert parsed_items[0]["end"] is None


def test_time_notes():
    assert parsed_items[0]["time_notes"] == "Confirm details with agency before attending"


def test_id():
    assert parsed_items[0]["id"
                           ] == "summ_regional_planning/201901160830/x/nefco_general_policy_board"


def test_status():
    assert parsed_items[0]["status"] == PASSED


def test_location():
    assert parsed_items[0]["location"] == {
        "name": "Summa Health Building (Classrooms 1 & 2)",
        "address": "3838 Massillon Rd, Green, OH 44685",
    }


def test_source():
    assert parsed_items[0]["source"] == test_response.url


def test_links():
    assert parsed_items[0]["links"] == []


def test_classification():
    assert parsed_items[0]["classification"] == BOARD


def test_all_day():
    assert parsed_items[0]["all_day"] is False
