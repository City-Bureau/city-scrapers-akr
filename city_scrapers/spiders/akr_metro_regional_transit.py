import re
from datetime import datetime

from city_scrapers_core.constants import BOARD
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider


class AkrMetroRegionalTransitSpider(CityScrapersSpider):
    name = "akr_metro_regional_transit"
    agency = "METRO Regional Transit Authority"
    timezone = "America/Detroit"
    start_urls = ["https://www.akronmetro.org/metro-board-meetings.aspx"]
    location = {
        "name": "Robert K. Pfaff Transit Center",
        "address": "631 S Broadway St, Akron, OH 44311",
    }

    def parse(self, response):
        """
        `parse` should always `yield` Meeting items.

        Change the `_parse_title`, `_parse_start`, etc methods to fit your scraping
        needs.
        """
        self._validate_start_time(response)
        self._validate_location(response)

        header_str = " ".join(response.css("#subpage-main h2 *::text").extract())
        year_str = re.search(r"\d{4}", header_str).group()

        # TODO: Find info for additional committees
        for item in response.css("#subpage-main h2 + ul")[:1].css("li"):
            start = self._parse_start(item, year_str)
            if not start:
                continue
            meeting = Meeting(
                title=self._parse_title(item),
                description="",
                classification=BOARD,
                start=start,
                end=None,
                all_day=False,
                time_notes="",
                location=self.location,
                links=self._parse_links(item, response),
                source=response.url,
            )

            meeting["status"] = self._get_status(
                meeting, text=" ".join(item.css("*::text").extract())
            )
            meeting["id"] = self._get_id(meeting)

            yield meeting

    def _parse_title(self, item):
        item_text = " ".join(item.css("*::text").extract())
        if "Committee" in item_text:
            return "Board of Trustees and Committees"
        return "Board of Trustees"

    def _parse_start(self, item, year_str):
        """Parse start datetime as a naive datetime object."""
        item_text = " ".join(item.css("*::text").extract())
        date_match = re.search(r"[A-Z][a-z]{2,9} \d{1,2}", item_text)
        time_match = re.search(r"[0-9]{1,2}(:\d{2})? [apm\.]{2,4}", item_text)
        if not date_match:
            return
        date_str = date_match.group()
        time_str = "9:00am"
        if time_match:
            time_str = re.sub(r"[\s\.]", "", time_match.group())
            if ":" not in time_str:
                time_str = re.sub(r"(\d+)", r"\1:00", time_str)
        return datetime.strptime(year_str + date_str + time_str, "%Y%B %d%I:%M%p")

    def _validate_start_time(self, response):
        desc_text = " ".join(response.css("#subpage-main *::text").extract())
        if "9 a.m." not in desc_text:
            raise ValueError("Meeting start time has changed")

    def _validate_location(self, response):
        desc_text = " ".join(response.css("#subpage-main *::text").extract())
        if "631" not in desc_text:
            raise ValueError("Meeting location has changed")

    def _parse_links(self, item, response):
        """Parse or generate links."""
        links = []
        for link in item.css("a"):
            link_title = " ".join(link.css("*::text").extract())
            if "Board Packet" in link_title:
                link_title = "Board Packet"
            links.append(
                {"title": link_title, "href": response.urljoin(link.attrib["href"])}
            )
        return links
