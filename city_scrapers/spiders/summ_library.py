from collections import defaultdict
from datetime import datetime

import scrapy
from city_scrapers_core.constants import BOARD
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider


class SummLibrarySpider(CityScrapersSpider):
    name = "summ_library"
    agency = "Akron-Summit County Public Library"
    timezone = "America/Detroit"
    allowed_domains = ["www.akronlibrary.org"]
    start_urls = ["https://www.akronlibrary.org/about/board-of-trustees/minutes"]

    def parse(self, response):
        self.minutes_map = self._parse_minutes(response)
        yield scrapy.Request(
            "https://www.akronlibrary.org/about/board-of-trustees/meetings",
            callback=self._parse_meetings,
            dont_filter=True,
        )

    def _parse_minutes(self, response):
        minutes_map = defaultdict(list)
        for minutes_col in response.css(".minutes .span2")[:2]:
            year_str = minutes_col.css("h3::text").extract_first().strip()
            for minutes in minutes_col.css("a"):
                link_str = minutes.attrib["data-content"]
                link_month = link_str.split()[0]
                link_title = " ".join(link_str.split()[2:])
                minutes_map[year_str + link_month].append({
                    "title": link_title,
                    "href": response.urljoin(minutes.attrib["href"]),
                })
        return minutes_map

    def _parse_meetings(self, response):
        """
        `parse` should always `yield` Meeting items.

        Change the `_parse_title`, `_parse_start`, etc methods to fit your scraping
        needs.
        """
        meetings_text = " ".join(response.css("#meetings *::text").extract())
        if "4:00 PM" not in meetings_text:
            raise ValueError("Meeting time has changed")

        for item in response.css("#meetings h4"):
            start = self._parse_start(item)
            meeting = Meeting(
                title="Board of Trustees",
                description="",
                classification=BOARD,
                start=self._parse_start(item),
                end=None,
                all_day=False,
                time_notes="",
                location=self._parse_location(item),
                links=self.minutes_map[start.strftime("%Y%B")],
                source=response.url,
            )

            meeting["status"] = self._get_status(meeting)
            meeting["id"] = self._get_id(meeting)

            yield meeting

    def _parse_start(self, item):
        """Parse start datetime as a naive datetime object."""
        date_str = " ".join(item.css("*::text").extract()).strip()
        return datetime.strptime(date_str + "4pm", "%B %d, %Y%I%p")

    def _parse_location(self, item):
        """Parse or generate location."""
        loc_str = item.xpath("./following-sibling::p[1]/text()").extract_first().strip()
        loc_split = loc_str.split(", ")
        return {
            "name": loc_split[0],
            "address": ", ".join(loc_split[1:]),
        }
