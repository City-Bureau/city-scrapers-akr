from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import BOARD, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.summ_alcohol_drug_mental_health import (
    SummAlcoholDrugMentalHealthSpider,
)

test_docs_response = file_response(
    join(dirname(__file__), "files", "summ_alcohol_drug_mental_health_minutes.html"),
    url="https://www.admboard.org/board-of-directors.aspx",
)
test_response = file_response(
    join(dirname(__file__), "files", "summ_alcohol_drug_mental_health.html"),
    url="https://tockify.com/jackstest/detail/249/1563917400000",
)
spider = SummAlcoholDrugMentalHealthSpider()

freezer = freeze_time("2019-12-21")
freezer.start()

spider.date_link_map = spider._parse_documents(test_docs_response)
parsed_item = [item for item in spider._parse_event(test_response)][0]

freezer.stop()


def test_title():
    assert parsed_item["title"] == "Board of Directors"


def test_description():
    assert parsed_item["description"] == ""


def test_start():
    assert parsed_item["start"] == datetime(2019, 7, 23, 17, 30)


def test_end():
    assert parsed_item["end"] == datetime(2019, 7, 23, 19, 30)


def test_time_notes():
    assert parsed_item["time_notes"] == ""


def test_id():
    assert (
        parsed_item["id"]
        == "summ_alcohol_drug_mental_health/201907231730/x/board_of_directors"
    )


def test_status():
    assert parsed_item["status"] == PASSED


def test_location():
    assert parsed_item["location"] == {
        "name": "Summit County Public Health Department Board Room",
        "address": "1867 W. Market Street, Entrance A, Akron, OH 44313",
    }


def test_source():
    assert parsed_item["source"] == test_response.url


def test_links():
    assert parsed_item["links"] == [
        {
            "href": "https://www.admboard.org/Data/Sites/25/Assets/pdfs/BOD Minutes/bod-min-7.23.19-final-app-09.24.19.pdf",  # noqa
            "title": "Minutes",
        },
        {
            "title": "Agenda",
            "href": "https://www.admboard.org/Data/Sites/25/adm-bod-mtg-notice-agenda-pkt-7.23.19.pdf",  # noqa
        },
    ]


def test_classification():
    assert parsed_item["classification"] == BOARD


def test_all_day():
    assert parsed_item["all_day"] is False
