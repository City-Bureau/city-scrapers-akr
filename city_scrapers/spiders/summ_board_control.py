from collections import defaultdict
from datetime import datetime

from city_scrapers_core.constants import BOARD
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider


class SummBoardControlSpider(CityScrapersSpider):
    name = "summ_board_control"
    agency = "Summit County Board of Control"
    timezone = "America/Detroit"
    start_urls = [
        "https://co.summitoh.net/index.php/offices/boards-agencies-a-commissions/board-of-control"  # noqa
    ]
    location = {
        "name": "Council Chambers",
        "address": "175 S Main St, Floor 7, Akron, OH 44308",
    }

    def parse(self, response):
        """
        `parse` should always `yield` Meeting items.

        Change the `_parse_title`, `_parse_start`, etc methods to fit your scraping
        needs.
        """
        date_link_map = defaultdict(list)

        for link in response.css("#sidebar a"):
            if (
                "agenda" not in link.attrib["href"].lower()
                and "minutes" not in link.attrib["href"].lower()
            ):
                continue
            link_title = (
                "Agenda" if "agenda" in link.attrib["href"].lower() else "Minutes"
            )
            start = self._parse_start(link)
            if not start:
                continue
            date_link_map[start].append(
                {"title": link_title, "href": response.urljoin(link.attrib["href"])}
            )

        start_list = sorted([k for k in date_link_map.keys() if k], reverse=True)
        # Use the most recent 20 meetings
        for start in start_list[:20]:
            meeting = Meeting(
                title="Board of Control",
                description="",
                classification=BOARD,
                start=start,
                end=None,
                all_day=False,
                time_notes="See agenda to confirm details",
                location=self.location,
                links=date_link_map[start],
                source=response.url,
            )

            meeting["status"] = self._get_status(meeting)
            meeting["id"] = self._get_id(meeting)

            yield meeting

    def _parse_start(self, item):
        """Parse start datetime as a naive datetime object."""
        date_str = " ".join(item.css("*::text").extract()).strip()
        if not date_str:
            return
        return datetime.strptime(date_str + "1030", "%m-%d-%y%H%M")
