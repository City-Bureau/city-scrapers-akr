import re
from datetime import datetime

from city_scrapers_core.constants import BOARD, COMMITTEE
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider
from scrapy import Selector


class SummRegionalPlanningSpider(CityScrapersSpider):
    name = "summ_regional_planning"
    agency = "Northeast Ohio Four County Regional Planning and Development Organization"
    timezone = "America/Detroit"
    start_urls = ["http://www.nefcoplanning.org/meetings.html"]

    def parse(self, response):
        """
        `parse` should always `yield` Meeting items.

        Change the `_parse_title`, `_parse_start`, etc methods to fit your scraping
        needs.
        """
        content = re.split(
            r"\<p.*\>_+\</p\>", " ".join(response.css("#main").extract()), 1
        )
        for section in content:
            sel = Selector(text=section)
            title = self._parse_title(sel)
            location = self._parse_location(section)
            year_str = re.search(r"\d{4}", section).group()
            time_str = "12:00am"
            time_match = re.search(r"\d{1,2}:\d{2} [apm\.]{2,4}", section)
            if time_match:
                time_str = re.sub(r"(\s+|\.)", "", time_match.group()).lower()

            for item in sel.css("td"):
                item_str = " ".join(item.css("*::text").extract())
                start = self._parse_start(item_str, time_str, year_str)
                if not start:
                    continue

                meeting = Meeting(
                    title=title,
                    description="",
                    classification=self._parse_classification(title),
                    start=start,
                    end=None,
                    all_day=False,
                    time_notes="Confirm details with agency before attending",
                    location=location,
                    links=[],
                    source=response.url,
                )

                meeting["status"] = self._get_status(meeting, text=item_str)
                meeting["id"] = self._get_id(meeting)

                yield meeting

    def _parse_title(self, item):
        """Parse or generate meeting title."""
        title_str = item.css("strong::text").extract_first().strip()
        return re.sub(r"\(.*?\)", "", title_str).strip()

    def _parse_classification(self, title):
        """Parse or generate classification from allowed options."""
        if "Board" in title:
            return BOARD
        return COMMITTEE

    def _parse_start(self, item_str, time_str, year_str):
        """Parse start datetime as a naive datetime object."""
        date_match = re.search(
            r"[A-Z][a-z]{2,8} \d{1,2}", re.sub(r"\s+", " ", item_str)
        )
        if not date_match:
            return
        return datetime.strptime(
            " ".join([date_match.group(), time_str, year_str]), "%B %d %I:%M%p %Y"
        )

    def _parse_location(self, section):
        """Parse or generate location."""
        if "3838" in section:
            return {
                "name": "Summa Health Building (Classrooms 1 & 2)",
                "address": "3838 Massillon Rd, Green, OH 44685",
            }
        if "2345" in section:
            return {
                "name": "The Natatorium",
                "address": "2345 4th Street, Cuyahoga Falls, OH 44221",
            }
        return {
            "name": "TBD",
            "address": "",
        }
