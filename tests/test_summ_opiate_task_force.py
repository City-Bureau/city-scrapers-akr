from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import COMMISSION, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.summ_opiate_task_force import SummOpiateTaskForceSpider

test_response = file_response(
    join(dirname(__file__), "files", "summ_opiate_task_force.html"),
    url="https://www.summitcountyaddictionhelp.org/opiate-task-force-members.aspx",
)
spider = SummOpiateTaskForceSpider()

freezer = freeze_time("2019-10-02")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]

freezer.stop()


def test_count():
    assert len(parsed_items) == 12


def test_title():
    assert parsed_items[0]["title"] == "Key Stakeholders Quarterly Meeting"


def test_description():
    assert parsed_items[0]["description"] == ""


def test_start():
    assert parsed_items[0]["start"] == datetime(2019, 3, 20, 16, 0)


def test_end():
    assert parsed_items[0]["end"] == datetime(2019, 3, 20, 17, 30)


def test_time_notes():
    assert parsed_items[0]["time_notes"] == ""


def test_id():
    assert (
        parsed_items[0]["id"]
        == "summ_opiate_task_force/201903201600/x/key_stakeholders_quarterly_meeting"
    )


def test_status():
    assert parsed_items[0]["status"] == PASSED


def test_location():
    assert parsed_items[0]["location"] == spider.location


def test_source():
    assert parsed_items[0]["source"] == test_response.url


def test_links():
    assert parsed_items[0]["links"] == [
        {
            "href": "https://www.summitcountyaddictionhelp.org/Data/Sites/19/meeting-notes/scoatf_pqm/otf-stakeholders-mtg-notes-3.20.19.pdf",  # noqa
            "title": "Minutes",
        }
    ]


def test_classification():
    assert parsed_items[0]["classification"] == COMMISSION


def test_all_day():
    assert parsed_items[0]["all_day"] is False
