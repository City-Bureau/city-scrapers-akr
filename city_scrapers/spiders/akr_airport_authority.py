import re
from datetime import datetime
from email import policy
from email.parser import BytesParser

from city_scrapers_core.constants import BOARD
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider


class AkrAirportAuthoritySpider(CityScrapersSpider):
    name = "akr_airport_authority"
    agency = "Akron-Canton Airport Authority"
    timezone = "America/Detroit"
    start_urls = [
        "https://city-scrapers-notice-emails.s3.amazonaws.com/akr_airport_authority/latest.eml"  # noqa
    ]
    location = {
        "name": "",
        "address": "5400 Lauby Rd. NW #9 North Canton, OH 44720",
    }

    def parse(self, response):
        """
        `parse` should always `yield` Meeting items.

        Change the `_parse_title`, `_parse_start`, etc methods to fit your scraping
        needs.
        """
        email_parser = BytesParser(policy=policy.default)
        parsed_email = email_parser.parsebytes(response.body)
        content = ""
        for part in parsed_email.iter_parts():
            if part.get_content_maintype() == "multipart":
                for sub_part in part.get_payload():
                    if sub_part.get_content_maintype() == "text":
                        content = sub_part.get_content()
                        break
        year_str = re.search(r"\d{4}", content).group()
        for date_str in re.findall(r"[A-Z][a-z]{2,8} \d{1,2}", content):
            start = self._parse_start(date_str, year_str)
            if not start:
                continue
            meeting = Meeting(
                title="Board of Trustees",
                description="",
                classification=BOARD,
                start=start,
                end=None,
                all_day=False,
                time_notes="Confirm meeting details with agency",
                location=self.location,
                links=[],
                source=response.url,
            )

            meeting["status"] = self._get_status(meeting)
            meeting["id"] = self._get_id(meeting)

            yield meeting

    def _parse_start(self, date_str, year_str):
        """Parse start datetime as a naive datetime object."""
        try:
            return datetime.strptime(date_str + year_str + "15", "%B %d%Y%H")
        except ValueError:
            return
