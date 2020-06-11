import re
from datetime import datetime
from io import BytesIO

from city_scrapers_core.constants import COMMISSION
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider
from PyPDF2 import PdfFileReader


class AkrPlanningSpider(CityScrapersSpider):
    name = "akr_planning"
    agency = "Akron City Planning Commission"
    timezone = "America/Detroit"
    start_urls = ["https://www.akronohio.gov/cms/site/2387094f0d307b46/index.html"]
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
                title="Planning Commission",
                description="",
                classification=COMMISSION,
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
        return datetime.strptime(date_str.title() + "9", "%B %d, %Y%H")
