import re

from city_scrapers_core.constants import BOARD, COMMITTEE, NOT_CLASSIFIED
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider
from dateutil.parser import parse


class AkrMetroRegionalTransitSpider(CityScrapersSpider):
    name = "akr_metro_regional_transit"
    agency = "METRO Regional Transit Authority"
    timezone = "America/Detroit"
    start_urls = ["https://www.akronmetro.org/metro-board-meetings.aspx"]
    location = {
        "name": "Robert K. Pfaff Transit Center",
        "address": "631 S Broadway St, Akron, OH 44311",
    }
    default_meeting_time = "9:00 am"

    def parse(self, response):
        """
        `parse` should always `yield` Meeting items.

        Change the `_parse_title`, `_parse_start`, etc methods to fit your scraping
        needs.
        """
        # get headers
        headers = []
        for header in response.css("section.main-copy h2"):
            header_text = header.css("::text").extract_first()
            if header_text:
                headers.append(header_text)

        # validation check
        if not headers:
            raise ValueError(
                "No headers found – agency's page structure may have changed."
            )

        # parse tables
        for idx, table in enumerate(response.css("section.main-copy table")):
            header = headers[idx]
            for item in table.css("tbody tr"):
                start = self._parse_start(item)
                if not start:
                    continue
                title = self._parse_title(header)
                meeting = Meeting(
                    title=title,
                    description="",
                    classification=self._parse_classification(header),
                    start=start,
                    end=None,
                    all_day=False,
                    time_notes="",
                    location=self.location,
                    links=self._parse_links(item),
                    source=response.url,
                )
                meeting["status"] = self._get_status(meeting)
                meeting["id"] = self._get_id(meeting)
                yield meeting

    def _parse_title(self, header):
        if "committee" in header.lower():
            return "Committee meeting"
        elif "board" in header.lower():
            return "Board meeting"
        return "Meeting"

    def _parse_start(self, item):
        """
        Get first column in each row and attempt to parse a
        date-like string
        """
        text = item.xpath(".//td[1]//text()").getall()
        start_str = " ".join([t.strip() for t in text if t.strip()])
        if not start_str:
            self.log("No start string found in row")
            return
        # target date-like text in format "February 20, 2024"
        date_str = re.search(r"[A-Z][a-z]+ \d{1,2}, \d{4}", start_str)
        date_str = date_str.group(0) if date_str else None
        if not date_str:
            return
        # attempt to target time-like text in a variety of formats
        # (eg. 12pm, 12:00pm, 12:00 pm)
        time_str = re.search(r"\d{1,2}(:\d{2})? ?[ap]m", start_str)
        time_str = time_str.group(0) if time_str else None
        # combine date and time strings, use default if no time string found
        start_str = f"{date_str} {time_str or self.default_meeting_time}"
        return parse(start_str)

    def _parse_classification(self, title):
        if "committee" in title.lower():
            return COMMITTEE
        if "board" in title.lower():
            return BOARD
        return NOT_CLASSIFIED

    def _parse_links(self, item):
        """
        Get links, if they exist, from the second and third columns
        in each row
        """
        second_col_links = item.css("td:nth-child(2) a")
        third_col_links = item.css("td:nth-child(3) a")
        links = []
        for link in second_col_links + third_col_links:
            links.append(
                {
                    "title": link.css("::text").extract_first(),
                    "href": link.attrib["href"],
                }
            )
        return links
