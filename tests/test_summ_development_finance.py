from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import BOARD, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.summ_development_finance import SummDevelopmentFinanceSpider

test_response = file_response(
    join(dirname(__file__), "files", "summ_development_finance.html"),
    url="http://www.developmentfinanceauthority.org/about/scheduled-meetings/",
)
test_schedule_response = file_response(
    join(dirname(__file__), "files", "summ_development_finance.docx"),
    url=(
        "http://www.developmentfinanceauthority.org/wp-content/uploads/2018/11/2019-DFA-mtg-schedule-PUBLIC-MEETING-NOTICE.docx"  # noqa
    ),
    mode="rb",
)
spider = SummDevelopmentFinanceSpider()

freezer = freeze_time("2019-10-10")
freezer.start()

spider.link_date_map = spider._parse_link_date_map(test_response)
parsed_items = [item for item in spider._parse_schedule(test_schedule_response)]

freezer.stop()


def test_count():
    assert len(parsed_items) == 24


def test_title():
    assert parsed_items[0]["title"] == "Board of Directors"


def test_description():
    assert parsed_items[0]["description"] == ""


def test_start():
    assert parsed_items[0]["start"] == datetime(2019, 1, 14, 8, 30)


def test_end():
    assert parsed_items[0]["end"] is None


def test_time_notes():
    assert parsed_items[0]["time_notes"] == "See source to confirm details"


def test_id():
    assert (
        parsed_items[0]["id"]
        == "summ_development_finance/201901140830/x/board_of_directors"
    )


def test_status():
    assert parsed_items[0]["status"] == PASSED


def test_location():
    assert parsed_items[0]["location"] == spider.location


def test_source():
    assert parsed_items[0]["source"] == test_response.url


def test_links():
    assert parsed_items[0]["links"] == []
    assert parsed_items[18]["links"] == [
        {
            "href": "http://www.developmentfinanceauthority.org/wp-content/uploads/2019/10/2019-10-15-Board-Agenda.docx",  # noqa
            "title": "Agenda",
        }
    ]


def test_classification():
    assert parsed_items[0]["classification"] == BOARD


def test_all_day():
    assert parsed_items[0]["all_day"] is False
