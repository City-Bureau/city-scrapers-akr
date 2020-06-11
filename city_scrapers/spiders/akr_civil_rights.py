import re
from datetime import datetime
from email.parser import BytesParser
from email.policy import default
from io import BytesIO, StringIO

from city_scrapers_core.constants import COMMISSION
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider
from pdfminer.high_level import extract_text_to_fp
from pdfminer.layout import LAParams


class AkrCivilRightsSpider(CityScrapersSpider):
    name = "akr_civil_rights"
    agency = "Akron Civil Rights Commission"
    timezone = "America/Detroit"
    start_urls = [
        "https://city-scrapers-notice-emails.s3.amazonaws.com/akr_civil_rights/latest.eml"  # noqa
    ]
    location = {
        "name": "Akron City Council, Meeting Room 1",
        "address": "166 S High Street, Akron OH 44308",
    }

    def parse(self, response):
        """
        `parse` should always `yield` Meeting items.

        Change the `_parse_title`, `_parse_start`, etc methods to fit your scraping
        needs.
        """
        msg = BytesParser(policy=default).parsebytes(response.body)
        attachments = list(msg.iter_attachments())
        pdf_list = [a for a in attachments if a.get_content_type() == "application/pdf"]
        if len(pdf_list) > 0:
            detail_text = self._parse_pdf_text(pdf_list[0].get_payload(decode=True))
        else:
            detail_text = self._parse_email_text(msg)

        yield self._parse_detail(detail_text)

    def _parse_pdf_text(self, pdf_bytes):
        lp = LAParams(line_margin=0.1)
        out_str = StringIO()
        extract_text_to_fp(BytesIO(pdf_bytes), out_str, laparams=lp)
        return re.sub(r"\s+", " ", out_str.getvalue()).strip()

    def _parse_email_text(self, msg):
        content = ""
        for part in msg.iter_parts():
            if part.get_content_maintype() == "multipart":
                for sub_part in part.get_payload():
                    if sub_part.get_content_maintype() == "text":
                        content = sub_part.get_content()
                        break
        return content

    def _parse_detail(self, detail):
        start = self._parse_start(detail)
        if not start:
            return
        meeting = Meeting(
            title="Civil Rights Commission",
            description="",
            classification=COMMISSION,
            start=start,
            end=None,
            all_day=False,
            time_notes="Confirm details with agency",
            location=self._parse_location(detail),
            links=[],
            source=self.start_urls[0],
        )

        meeting["status"] = self._get_status(meeting, text=detail)
        meeting["id"] = self._get_id(meeting)
        return meeting

    def _parse_start(self, detail):
        """Parse start datetime as a naive datetime object."""
        all_date_strs = re.findall(r"[A-Z][a-z]{2,8} \d{1,2},? \d{4}", detail)
        # Get all date strings that aren't followed by "Notice"
        # (meaning they aren't the intro)
        date_strs = re.findall(r"[A-Z][a-z]{2,8} \d{1,2},? \d{4}(?! Notice)", detail)
        # Return nothing if no dates found
        if len(all_date_strs) == 0 or len(date_strs) == 0:
            return
        if len(date_strs) >= 1:
            date_str = date_strs[0]
        # If there are two date strings and all matched, skip the first because it
        # likely means the check against the document date failed
        if len(date_strs) == 2 and len(all_date_strs) == 2:
            date_str = date_strs[1]
        time_strs = [
            s[0]
            for s in re.findall(r"(\d{1,2}(:\d{2}) [apm\.]{2,4})", detail, flags=re.I)
        ]
        time_str = "12:00 am"
        if len(time_strs) > 0:
            time_str = time_strs[0].replace(".", "").lower()
        dt_fmt = "%B %d %Y%I:%M %p"
        if ":" not in time_str:
            dt_fmt = "%B %d %Y%I %p"
        return datetime.strptime(date_str.replace(",", "") + time_str, dt_fmt)

    def _parse_location(self, detail):
        """Parse or generate location."""
        loc_list = re.findall(r"\d{2,5} [A-Z][A-Za-z\d\., ]{10,50}?\d{5}", detail)
        if len(loc_list) == 0 or "166" in loc_list[0]:
            return self.location
        return {
            "name": "",
            "address": loc_list[0],
        }
