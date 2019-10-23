import re
from datetime import datetime

from city_scrapers_core.constants import BOARD, COMMITTEE
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider


class SummReworksSpider(CityScrapersSpider):
    name = "summ_reworks"
    agency = "Summit County ReWorks"
    timezone = "America/Detroit"
    start_urls = ["http://www.summitreworks.com/events/"]
    location = {
        "name": "Summit County Public Health",
        "address": "1867 W Market St, Akron, OH 44313",
    }

    def parse(self, response):
        """
        `parse` should always `yield` Meeting items.

        Change the `_parse_title`, `_parse_start`, etc methods to fit your scraping
        needs.
        """
        for item in response.css(".barItemDetail"):
            title = self._parse_title(item)
            if "Invitation" in title or ("Board" not in title and "Committee" not in title):
                continue
            self._validate_location(item)
            meeting = Meeting(
                title=title,
                description="",
                classification=self._parse_classification(title),
                start=self._parse_start(item),
                end=None,
                all_day=False,
                time_notes="",
                location=self.location,
                links=[],
                source=response.url,
            )

            meeting["status"] = self._get_status(
                meeting, text=" ".join(item.css("*::text").extract())
            )
            meeting["id"] = self._get_id(meeting)

            yield meeting

    def _parse_title(self, item):
        """Parse or generate meeting title."""
        title_str = item.css(".barItemDetailHeading::text").extract_first().strip()
        return re.sub(r"(ReWorks'?|Meeting)", "", title_str).strip()

    def _parse_classification(self, title):
        """Parse or generate classification from allowed options."""
        if "Committee" in title:
            return COMMITTEE
        return BOARD

    def _parse_start(self, item):
        """Parse start datetime as a naive datetime object."""
        dt_str = " ".join(item.css(".barItemDate *::text").extract()).strip()
        return datetime.strptime(dt_str.replace(".", ""), "%B %d, %Y, %I:%M %p")

    def _validate_location(self, item):
        """Parse or generate location."""
        if "1867" not in " ".join(item.css("*::text").extract()):
            raise ValueError("Meeting location has changed")
