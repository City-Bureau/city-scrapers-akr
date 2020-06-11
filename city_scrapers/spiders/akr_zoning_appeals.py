import re
from datetime import datetime
from io import BytesIO

from city_scrapers_core.constants import BOARD
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider
from PyPDF2 import PdfFileReader


class AkrZoningAppealsSpider(CityScrapersSpider):
    name = "akr_zoning_appeals"
    agency = "Akron Board of Zoning Appeals"
    timezone = "America/Detroit"
    start_urls = ["https://www.akronohio.gov/cms/site/462db8daed9dd330/index.html"]
    location = {
        "name": "Akron City Hall",
        "address": "166 S High St, Akron, OH 44308",
    }

    def parse(self, response):
        """
        `parse` should always `yield` Meeting items.

        Change the `_parse_title`, `_parse_start`, etc methods to fit your scraping
        needs.
        """
        for link in response.css("#mainColumn a"):
            if "Calendar" in " ".join(link.css("*::text").extract()):
                yield response.follow(
                    link.attrib["href"], callback=self._parse_calendar, dont_filter=True
                )

    def _parse_calendar(self, response):
        """Parse dates and details from schedule PDF"""
        pdf_obj = PdfFileReader(BytesIO(response.body))
        pdf_text = re.sub(r"\s+", " ", pdf_obj.getPage(0).extractText()).replace(
            " ,", ","
        )

        for idx, date_str in enumerate(
            re.findall(r"[a-zA-Z]{3,10} \d{1,2}, \d{4}", pdf_text)
        ):
            # Ignore every other item
            if idx % 2 == 1:
                continue
            meeting = Meeting(
                title="Board of Zoning Appeals",
                description="",
                classification=BOARD,
                start=self._parse_start(date_str),
                end=None,
                all_day=False,
                time_notes="Confirm details with agency",
                location=self.location,
                links=[],
                source=self.start_urls[0],
            )

            meeting["status"] = self._get_status(meeting)
            meeting["id"] = self._get_id(meeting)

            yield meeting

    def _parse_start(self, date_str):
        """Parse start datetime as a naive datetime object."""
        return datetime.strptime(date_str.title() + "15", "%B %d, %Y%H")
