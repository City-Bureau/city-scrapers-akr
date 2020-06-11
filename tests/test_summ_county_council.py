from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import CITY_COUNCIL, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.summ_county_council import SummCountyCouncilSpider

test_response = file_response(
    join(dirname(__file__), "files", "summ_county_council.html"),
    url=(
        "https://council.summitoh.net/phpicalendar/month.php?cal=County_of_Summit_County_Council_Events_Calendar&getdate=20190925"  # noqa
    ),
)
test_links_response = file_response(
    join(dirname(__file__), "files", "summ_county_council_links.html"),
    url="https://council.summitoh.net/index.php/legislative-information/agendas/committee/2019",  # noqa
)
spider = SummCountyCouncilSpider()

freezer = freeze_time("2019-09-21")
freezer.start()

spider._parse_documents(test_links_response)
parsed_items = [item for item in spider._parse_calendar(test_response)]

freezer.stop()


def test_count():
    assert len(list(spider.link_map.keys())) == 18
    assert len(parsed_items) == 5


def test_title():
    assert parsed_items[0]["title"] == "County Council"


def test_description():
    assert parsed_items[0]["description"] == ""


def test_start():
    assert parsed_items[0]["start"] == datetime(2019, 9, 2, 16, 30)


def test_end():
    assert parsed_items[0]["end"] == datetime(2019, 9, 2, 17, 30)


def test_time_notes():
    assert parsed_items[0]["time_notes"] == ""


def test_id():
    assert parsed_items[0]["id"] == "summ_county_council/201909021630/x/county_council"


def test_status():
    assert parsed_items[0]["status"] == PASSED


def test_location():
    assert parsed_items[0]["location"] == spider.location


def test_source():
    assert parsed_items[0]["source"] == test_response.url


def test_links():
    assert parsed_items[0]["links"] == []
    assert parsed_items[2]["links"] == [
        {
            "title": "Agenda",
            "href": "https://council.summitoh.net/index.php/legislative-information/agendas/committee/2019/finish/145/10551",  # noqa
        }
    ]


def test_classification():
    assert parsed_items[0]["classification"] == CITY_COUNCIL


def test_all_day():
    assert parsed_items[0]["all_day"] is False
