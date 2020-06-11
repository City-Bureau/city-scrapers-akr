import re
from datetime import datetime
from email.parser import BytesParser
from email.policy import default

from city_scrapers_core.constants import COMMISSION
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider


class AkrCivilServiceSpider(CityScrapersSpider):
    name = "akr_civil_service"
    agency = "Akron Civil Service Commission"
    timezone = "America/Detroit"
    start_urls = [
        "https://city-scrapers-notice-emails.s3.amazonaws.com/akr_civil_service/latest.eml"  # noqa
    ]
    location = {
        "name": "City Hall, Council Chambers",
        "address": "166 South High St Akron, OH 44308",
    }

    def parse(self, response):
        """
        `parse` should always `yield` Meeting items.

        Change the `_parse_title`, `_parse_start`, etc methods to fit your scraping
        needs.
        """
        msg = BytesParser(policy=default).parsebytes(response.body)
        detail_text = self._parse_email_text(msg)
        start = self._parse_start(detail_text)
        if not start:
            return
        meeting = Meeting(
            title="Commission",
            description="",
            classification=COMMISSION,
            start=start,
            end=None,
            all_day=False,
            time_notes="Confirm details with agency",
            location=self.location,
            links=[],
            source=response.url,
        )

        meeting["status"] = self._get_status(meeting, text=detail_text)
        meeting["id"] = self._get_id(meeting)

        yield meeting

    def _parse_email_text(self, msg):
        content = ""
        for part in msg.iter_parts():
            if part.get_content_maintype() == "multipart":
                for sub_part in part.get_payload():
                    if sub_part.get_content_maintype() == "text":
                        content = sub_part.get_content()
                        break
        return content

    def _parse_start(self, text):
        """Parse start datetime as a naive datetime object."""
        start_date_match = re.search(r"[A-Z][a-z]{2,8} \d{1,2},? \d{4}", text)
        # Intentionally triggering error if unable to parse start date
        start_date_str = start_date_match.group().replace(",", "")
        start_time_match = re.search(r"\d{1,2}(\:\d{2})? ?[APMapm\.]{2,4}", text)
        if start_time_match:
            start_time_str = re.sub(r"[\s\.]", "", start_time_match.group().lower())
        else:
            start_time_str = "12:00am"
        time_fmt = "%I%p"
        if ":" in start_time_str:
            time_fmt = "%I:%M%p"

        return datetime.strptime(
            " ".join([start_date_str, start_time_str]), "%B %d %Y " + time_fmt
        )
