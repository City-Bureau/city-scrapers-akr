from city_scrapers_core.constants import BOARD
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider
from dateutil.parser import parse


class SummLibrarySpider(CityScrapersSpider):
    name = "summ_library"
    agency = "Akron-Summit County Public Library"
    timezone = "America/Detroit"
    start_urls = ["https://www.akronlibrary.org/about/board-of-trustees/meetings"]
    default_start_time = "4:30 PM"
    default_links = {
        "title": "Minutes page",
        "href": "https://www.akronlibrary.org/about/board-of-trustees/minutes",
    }

    def parse(self, response):
        meetings_text = " ".join(response.css("#meetings *::text").extract())
        if self.default_start_time not in meetings_text:
            raise ValueError("Meeting time has changed")

        for item in response.css("#meetings h4"):
            start = self._parse_start(item)
            if not start:
                continue
            meeting = Meeting(
                title="Board of Trustees",
                description="",
                classification=BOARD,
                start=self._parse_start(item),
                end=None,
                all_day=False,
                time_notes="",
                location=self._parse_location(item),
                links=self.default_links,
                source=response.url,
            )

            meeting["status"] = self._get_status(meeting)
            meeting["id"] = self._get_id(meeting)

            yield meeting

    def _parse_start(self, item):
        """Parse start datetime as a naive datetime object."""
        date_str = " ".join(item.css("*::text").extract()).strip()
        datetime_str = f"{date_str} {self.default_start_time}"
        return parse(datetime_str, fuzzy=True)

    def _parse_location(self, item):
        """Parse or generate location."""
        loc_str = item.xpath("./following-sibling::p[1]/text()").extract_first().strip()
        loc_split = loc_str.split(", ")
        return {
            "name": loc_split[0],
            "address": ", ".join(loc_split[1:]),
        }
