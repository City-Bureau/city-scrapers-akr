from datetime import datetime
from os.path import dirname, join
from unittest.mock import MagicMock

import pytest
from city_scrapers_core.constants import BOARD, TENTATIVE
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.summ_land_bank import SummLandBankSpider

test_response = file_response(
    join(dirname(__file__), "files", "summ_land_bank.html"),
    url="http://www.summitlandbank.org/board-meeting-notices",
)
test_agenda_response = file_response(
    join(dirname(__file__), "files", "summ_land_bank_agendas.html"),
    url="http://www.summitlandbank.org/board-meeting-agendas",
)
test_notice_response = file_response(
    join(dirname(__file__), "files", "summ_land_bank.pdf"),
    url=(
        "https://static1.squarespace.com/static/563cae01e4b0de6b06b1e023/t/5c9cd00ae79c70c4d6913817/1553780746707/SCLRC+Public+Notice+03-29-19.pdf"  # noqa
    ),
    mode="rb"
)

spider = SummLandBankSpider()

freezer = freeze_time("2019-10-14")
freezer.start()

spider._parse_documents(test_agenda_response)
parsed_items = [item for item in spider._parse_notice_page(test_response) if item]

freezer.stop()


@pytest.fixture()
def parsed_item(monkeypatch):
    freezer.start()
    req = MagicMock()
    req.meta = {"meeting_text": "March 29, 2019", "source": test_response.url}
    monkeypatch.setattr(test_notice_response, "request", req)
    parsed_item = [item for item in spider._parse_notice(test_notice_response)][0]
    freezer.stop()
    return parsed_item


def test_count():
    assert len(parsed_items) == 7


def test_title(parsed_item):
    assert parsed_items[-1]["title"] == "Board of Directors"
    assert parsed_item["title"] == "Board of Directors Meeting and Retreat"


def test_description(parsed_item):
    assert parsed_item["description"] == ""


def test_start(parsed_item):
    assert parsed_items[-1]["start"] == datetime(2019, 11, 21, 14, 0)
    assert parsed_item["start"] == datetime(2019, 3, 29, 9, 0)


def test_end(parsed_item):
    assert parsed_item["end"] is None


def test_time_notes(parsed_item):
    assert parsed_item["time_notes"] == "Confirm details in source"


def test_id(parsed_item):
    assert parsed_item["id"
                       ] == "summ_land_bank/201903290900/x/board_of_directors_meeting_and_retreat"


def test_status():
    assert parsed_items[-1]["status"] == TENTATIVE


def test_location(parsed_item):
    assert parsed_items[-1]["location"] == spider.location
    assert parsed_item["location"] == {
        "name": "",
        "address": "1180 South Main Street, Room 382, Akron, OH 44301",
    }


def test_source(parsed_item):
    assert parsed_items[-1]["source"] == test_response.url
    assert parsed_item["source"] == test_response.url


def test_links(parsed_item):
    assert parsed_item["links"] == [
        {
            "href": "http://www.summitlandbank.org/s/SLCRC-DRAFT-Agenda-03-29-19-3m3l.pdf",
            "title": "Agenda"
        },
        {
            "href":
                "https://static1.squarespace.com/static/563cae01e4b0de6b06b1e023/t/5c9cd00ae79c70c4d6913817/1553780746707/SCLRC+Public+Notice+03-29-19.pdf",  # noqa
            "title": "Notice"
        }
    ]


def test_classification(parsed_item):
    assert parsed_item["classification"] == BOARD


def test_all_day(parsed_item):
    assert parsed_item["all_day"] is False
