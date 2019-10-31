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


class AkrSeniorCitizensSpider(CityScrapersSpider):
    name = "akr_senior_citizens"
    agency = "Akron Senior Citizens Commission"
    timezone = "America/Detroit"
    start_urls = [
        "https://city-scrapers-notice-emails.s3.amazonaws.com/akr_senior_citizens/latest.eml"
    ]
    location = {
        "name": "Akron-Summit County Public Library (Meeting Room 2AB)",
        "address": "60 S Main St Akron, OH 44308",
    }

    def parse(self, response):
        msg = BytesParser(policy=default).parsebytes(response.body)
        attachments = list(msg.iter_attachments())
        pdf_list = [a for a in attachments if a.get_content_type() == "application/pdf"]
        # List of tuples of filename, match string
        match_list = []

        for pdf_obj in pdf_list:
            pdf_text = self._parse_pdf_text(pdf_obj.get_payload(decode=True))
            meeting_match = re.search(
                r"Senior Citizens\s+Commission\n.*?(?=\n\n)",
                pdf_text,
                flags=re.I | re.M | re.DOTALL,
            )
            if meeting_match:
                match_list.append((pdf_obj.get_filename(), meeting_match.group()))

        if len(match_list) == 0:
            raise ValueError("Meeting not found in {} PDFs".format(len(pdf_list)))

        for pdf_name, meeting_str in match_list:
            year_match = re.search(r"\d{4}", pdf_list[0].get_filename())
            year_str = None
            if year_match:
                year_str = year_match.group()
            start, end = self._parse_times(meeting_str, year_str)
            if not start:
                return
            meeting = Meeting(
                title="Senior Citizens Commission",
                description="",
                classification=COMMISSION,
                start=start,
                end=end,
                all_day=False,
                time_notes="",
                location=self._parse_location(meeting_str),
                links=[],
                source=response.url,
            )

            meeting["status"] = self._get_status(meeting, text=meeting_str)
            meeting["id"] = self._get_id(meeting)

            yield meeting

    def _parse_pdf_text(self, pdf_bytes):
        lp = LAParams(line_margin=5.0)
        out_str = StringIO()
        extract_text_to_fp(BytesIO(pdf_bytes), out_str, laparams=lp)
        return re.sub(r"[ \t\r]+(?=\n)", "", re.sub(r"[ \t\r]+", " ", out_str.getvalue()))

    def _parse_times(self, meeting_str, year_str):
        """Parse start, end datetimes as naive datetime objects."""
        if not year_str:
            year_str = str(datetime.now().year)
        date_match = re.search(r"[A-Z][a-z]{2,7} \d{1,2}", meeting_str)
        time_strs = [
            t[0] for t in
            re.findall(r"(\d{1,2}( ?[apm\.]{2,4}|:\d{2} ?[apm\.]{2,4}))", meeting_str, flags=re.I)
        ]
        if not (date_match or len(time_strs) == 0):
            return
        date_str = date_match.group()
        start = self._parse_dt_str(date_str, time_strs[0], year_str)
        end = None
        if len(time_strs) > 1:
            end = self._parse_dt_str(date_str, time_strs[1], year_str)
        return start, end

    def _parse_dt_str(self, date_str, time_str, year_str):
        clean_time_str = re.sub(r"[\.\s]", "", time_str)
        dt_fmt = "%B %d %I:%M%p %Y"
        if ":" not in clean_time_str:
            dt_fmt = "%B %d %I%p %Y"
        return datetime.strptime(" ".join([date_str, time_str, year_str]), dt_fmt)

    def _parse_location(self, meeting_str):
        """Parse or generate location."""
        split_desc = re.split(r"(?<=[m\.])\n", meeting_str, 1, flags=re.I | re.M)
        if "2AB" in meeting_str or len(split_desc) < 2:
            return self.location
        loc_str = split_desc[1]
        split_loc = re.split(r"\n(?=\d)", loc_str, flags=re.M)
        loc_name = ""
        if len(split_loc) == 1:
            loc_addr = split_loc[0]
        else:
            loc_name = split_loc[0]
            loc_addr = split_loc[1]
        loc_addr = loc_addr.replace(" Downtown", "")
        if "OH" not in loc_addr:
            loc_addr += " OH"
        return {
            "name": loc_name,
            "address": loc_addr,
        }
