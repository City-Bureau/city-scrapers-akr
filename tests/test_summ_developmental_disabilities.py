from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import BOARD, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.summ_developmental_disabilities import (
    SummDevelopmentalDisabilitiesSpider,
)

test_response = file_response(
    join(dirname(__file__), "files", "summ_developmental_disabilities.json"),
    url=(
        "http://www.summitdd.org/wp-admin/admin-ajax.php?action=WP_FullCalendar&type=event&event-categories=30&start=2019-09-30&end=2019-11-11"  # noqa
    ),
)
test_detail_response = file_response(
    join(dirname(__file__), "files", "summ_developmental_disabilities_detail.html"),
    url="http://www.summitdd.org/resources/events/september-board-meeting-2019/",
)
test_link_response = file_response(
    join(dirname(__file__), "files", "summ_developmental_disabilities_links.html"),
    url=(
        "http://www.summitdd.org/about/summit-dd-board/board-meetings/2019-meeting-documents/september-board-meeting-documents/"  # noqa
    ),
)
spider = SummDevelopmentalDisabilitiesSpider()

freezer = freeze_time("2019-10-05")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]
for item in spider._parse_detail(test_detail_response):
    continue
parsed_item = [item for item in spider._parse_links(test_link_response)][0]

freezer.stop()


def test_count():
    assert len(parsed_items) == 1


def test_title():
    assert parsed_item["title"] == "Developmental Disabilities Board"


def test_description():
    assert parsed_item["description"] == ""


def test_start():
    assert parsed_item["start"] == datetime(2019, 9, 26, 17, 30)


def test_end():
    assert parsed_item["end"] is None


def test_time_notes():
    assert parsed_item["time_notes"] == ""


def test_id():
    assert (
        parsed_item["id"]
        == "summ_developmental_disabilities/201909261730/x/developmental_disabilities_board"  # noqa
    )


def test_status():
    assert parsed_item["status"] == PASSED


def test_location():
    assert parsed_item["location"] == {
        "name": "Summit DD Administration - Board Room",
        "address": "89 E. Howe Road Tallmadge, OH 44278",
    }


def test_source():
    assert parsed_item["source"] == test_detail_response.url


def test_links():
    assert parsed_item["links"] == [
        {
            "href": "https://s3-us-east-2.amazonaws.com/s3.summitdd.org/wp-content/uploads/2019/09/Agenda-September-2019.pdf",  # noqa
            "title": "Agenda - September 2019",
        },
        {
            "href": "https://s3-us-east-2.amazonaws.com/s3.summitdd.org/wp-content/uploads/2019/09/SUNSHINE-LAW-NOTICE.pdf",  # noqa
            "title": "SUNSHINE LAW NOTICE",
        },
        {
            "href": "https://s3-us-east-2.amazonaws.com/s3.summitdd.org/wp-content/uploads/2019/09/Board-Packet-September-2019.pdf",  # noqa
            "title": "Board Packet - September 2019",
        },
    ]


def test_classification():
    assert parsed_item["classification"] == BOARD


def test_all_day():
    assert parsed_item["all_day"] is False
