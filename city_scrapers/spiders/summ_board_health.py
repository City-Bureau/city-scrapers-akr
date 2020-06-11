import re
from collections import defaultdict
from datetime import datetime

from city_scrapers_core.constants import BOARD
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider


class SummBoardHealthSpider(CityScrapersSpider):
    name = "summ_board_health"
    agency = "Summit County Board of Health"
    timezone = "America/Detroit"
    start_urls = ["https://www.scph.org/board-health"]
    location = {
        "name": "Summit County Public Health Department Boardroom",
        "address": "1867 W Market St, Akron, OH 44313",
    }

    def parse(self, response):
        """
        `parse` should always `yield` Meeting items.

        Change the `_parse_title`, `_parse_start`, etc methods to fit your scraping
        needs.
        """
        link_date_map = defaultdict(list)

        for link in response.css("article p a"):
            link_href = response.urljoin(link.attrib["href"])
            if "agenda" not in link_href.lower() and "minutes" not in link_href.lower():
                continue
            link_title = "Agenda" if "agenda" in link_href.lower() else "Minutes"
            start = self._parse_start(link_href)
            if not start:
                continue
            link_date_map[start].append({"title": link_title, "href": link_href})

        for start, links in link_date_map.items():
            meeting = Meeting(
                title="Board of Health",
                description="",
                classification=BOARD,
                start=start,
                end=None,
                all_day=False,
                time_notes="",
                location=self.location,
                links=links,
                source=response.url,
            )

            meeting["status"] = self._get_status(meeting)
            meeting["id"] = self._get_id(meeting)

            yield meeting

    def _parse_start(self, link):
        """Parse start datetime as a naive datetime object."""
        link_str = link.replace("%20", " ")
        agenda_match = re.search(r"(?<=/)\d{1,2} \d{1,2} \d{2}", link_str)
        minutes_match = re.search(r"(?<=/)[A-Za-z]{3,9} \d{1,2} \d{4}", link_str)
        if agenda_match:
            return datetime.strptime(agenda_match.group() + "17", "%m %d %y%H")
        if minutes_match:
            return datetime.strptime(minutes_match.group() + "17", "%B %d %Y%H")
