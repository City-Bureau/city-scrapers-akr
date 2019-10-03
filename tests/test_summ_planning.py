from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import COMMISSION, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.summ_planning import SummPlanningSpider

test_docs_response = file_response(
    join(dirname(__file__), "files", "summ_planning.html"),
    url="https://co.summitoh.net/index.php/departments/community-a-economic-development/planning",
)
test_response = file_response(
    join(dirname(__file__), "files", "summ_planning.pdf"),
    url=(
        "https://co.summitoh.net/images/stories/Development/Planning/Meeting/2019/2019_SCPC_mting_and_submit_deadlines.pdf"  # noqa
    ),
    mode="rb",
)
spider = SummPlanningSpider()

freezer = freeze_time("2019-09-30")
freezer.start()

section = spider._parse_section(test_docs_response)
spider.link_date_map = spider._parse_links_page(section, test_docs_response)
parsed_items = [item for item in spider._parse_pdf_schedule(test_response)]

freezer.stop()


def test_count():
    assert len(parsed_items) == 12


def test_title():
    assert parsed_items[0]["title"] == "Planning Commission"


def test_description():
    assert parsed_items[0]["description"] == ""


def test_start():
    assert parsed_items[0]["start"] == datetime(2019, 1, 24, 15, 0)


def test_end():
    assert parsed_items[0]["end"] is None


def test_time_notes():
    assert parsed_items[0]["time_notes"] == ""


def test_id():
    assert parsed_items[0]["id"] == "summ_planning/201901241500/x/planning_commission"


def test_status():
    assert parsed_items[0]["status"] == PASSED


def test_location():
    assert parsed_items[0]["location"] == spider.location


def test_source():
    assert parsed_items[0]["source"] == spider.start_urls[0]


def test_links():
    assert parsed_items[0]["links"] == [{
        "href":
            "https://co.summitoh.net/images/stories/Development/Planning/Meeting/2019/January242019_SCPC_Packet.pdf",  # noqa
        "title": "Meeting Packet"
    }]


def test_classification():
    assert parsed_items[0]["classification"] == COMMISSION


def test_all_day():
    assert parsed_items[0]["all_day"] is False
