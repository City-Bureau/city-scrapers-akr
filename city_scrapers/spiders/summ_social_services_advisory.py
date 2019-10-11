import re
from datetime import datetime, timedelta
from email.parser import BytesParser
from email.policy import default
from io import BytesIO, StringIO
from zipfile import ZipFile

from city_scrapers_core.constants import ADVISORY_COMMITTEE, COMMITTEE
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider
from scrapy import Selector


class SummSocialServicesAdvisorySpider(CityScrapersSpider):
    name = "summ_social_services_advisory"
    agency = "Summit County Social Services Advisory Board"
    timezone = "America/Detroit"
    start_urls = [
        "https://city-scrapers-notice-emails.s3.amazonaws.com/summ_social_services_advisory/latest.eml"  # noqa
    ]
    location = {
        "name": "Summit County Public Health",
        "address": "1867 W Market St, Akron, OH 44313",
    }

    def parse(self, response):
        """
        `parse` should always `yield` Meeting items.

        Change the `_parse_title`, `_parse_start`, etc methods to fit your scraping
        needs.
        """
        msg = BytesParser(policy=default).parsebytes(response.body)
        attachments = list(msg.iter_attachments())
        docx_list = [a for a in attachments if ".docx" in a.get_filename()]
        items = []
        if len(docx_list) > 0:
            items.extend(self._parse_docx(docx_list[0].get_payload(decode=True)))
        items.extend(self._parse_email_text(msg))
        yield from self._parse_meetings(items)

    def _parse_docx(self, attachment):
        items = []
        docx_bytes = BytesIO(attachment)
        docx_str = ""
        with ZipFile(docx_bytes) as zf:
            for zip_info in zf.infolist():
                if zip_info.filename == "word/document.xml":
                    with zf.open(zip_info) as docx_file:
                        docx_str = StringIO(docx_file.read().decode())
        if not docx_str:
            return
        # Remove MS Word namespaces on tags to use selectors
        sel = Selector(text=docx_str.getvalue())
        sel.remove_namespaces()
        year_str = "".join([
            p.strip()
            for p in sel.css("tbl > tr")[:1].css("tc:first-of-type")[:1].css("*::text").extract()
            if p.strip()
        ])
        for table in sel.css("tbl"):
            month_str = "".join([
                p.strip()
                for p in table.css("tr")[1:2].css("tc:first-of-type")[:1].css("*::text").extract()
                if p.strip()
            ]).title()
            for cell in table.css("tc > p"):
                cell_str = re.sub(
                    r"((?<=[\-–]) | (?=[\-–])|@)", "",
                    re.sub(r"\s+", " ", " ".join(cell.css("*::text").extract())).strip()
                ).strip()
                if (
                    len(cell_str) <= 2 or (len(cell_str) > 2 and cell_str.startswith("201"))
                    or not cell_str[0].isdigit()
                ):
                    continue
                items.append(self._parse_item(cell_str, month_str, year_str))
        return items

    def _parse_email_text(self, msg):
        items = []
        content = ""
        for part in msg.iter_parts():
            if part.get_content_maintype() == "multipart":
                for sub_part in part.get_payload():
                    if sub_part.get_content_maintype() == "text":
                        content = sub_part.get_content()
                        break
        if not content.strip():
            return items
        default_year = msg["date"].datetime.year
        date_match = re.search(
            r"(?P<month_day>[A-Z][a-z]{2,8} \d{1,2})[,\.a-z]+ ?(?P<year>\d{4})?", content
        )
        if not date_match:
            return items
        month_day_str = date_match.group("month_day")
        year_str = date_match.group("year")
        if not year_str:
            year_str = str(default_year)
        time_strs = [
            s[0].replace(" ", "") for s in re.findall(r"(\d{1,2}(:\d{2})? ?[apm\.]{2,4})", content)
        ]
        # Remove email signature working hours
        if "working hours" in content:
            time_strs = time_strs[:-10]
        start = None
        end = None
        if len(time_strs) > 0:
            time_fmt = "%I%p"
            if ":" in time_strs[0]:
                time_fmt = "%I:%M%p"

            start = datetime.strptime(
                " ".join([month_day_str, year_str, time_strs[0]]), "%B %d %Y " + time_fmt
            )
        if len(time_strs) > 1:
            time_fmt = "%I%p"
            if ":" in time_strs[1]:
                time_fmt = "%I:%M%p"

            end = datetime.strptime(
                " ".join([month_day_str, year_str, time_strs[1]]), "%B %d %Y " + time_fmt
            )

        if "special" in content.lower():
            title = "Special Board Meeting"
        else:
            title = "Advisory Board"
        if start:
            items = [(title, start, end)]

        return items

    def _parse_meetings(self, items):
        for title, start, end in items:
            if not title or not start:
                continue
            meeting = Meeting(
                title=title,
                description="",
                classification=self._parse_classification(title),
                start=start,
                end=end,
                all_day=False,
                time_notes="Confirm details with agency",
                location=self.location,
                links=[],
                source=self.start_urls[0],
            )

            meeting["status"] = self._get_status(meeting)
            meeting["id"] = self._get_id(meeting)

            yield meeting

    def _parse_title(self, item_str):
        """Parse or generate meeting title."""
        if "HHS" in item_str:
            return "Health and Human Services Committee"
        if "B&L" in item_str:
            return "Budget and Levy Committee"
        if "Exec" in item_str:
            return "Executive Committee"
        if "SSAB" in item_str or "Board" in item_str:
            return "Advisory Board"

    def _parse_classification(self, title):
        """Parse or generate classification from allowed options."""
        if "Committee" in title:
            return COMMITTEE
        return ADVISORY_COMMITTEE

    def _parse_item(self, item_str, month_str, year_str):
        """Returns tuple of title, start, end"""
        item_match = re.search(
            r"(?P<day>\d+) (?P<name>[A-Za-z& ]+) (?P<start>[\d:]+)[\-–]?(?P<end>[\d: apm\.]+)?",
            item_str
        )
        if not item_match:
            return None, None, None
        day_str = item_match.group("day")
        name_str = item_match.group("name")
        start, end = self._parse_start_end(
            " ".join([day_str, month_str, year_str]),
            item_match.group("start"),
            item_match.group("end"),
        )
        return self._parse_title(name_str), start, end

    def _parse_start_end(self, date_str, start_match, end_match):
        """Parse start, end datetimes as naive datetime objects."""
        dt_obj = datetime.strptime(date_str, "%d %B %Y")
        if not start_match:
            return dt_obj, None
        start_str = start_match
        end_str = end_match or ""
        if "a" in end_str or "p" in end_str:
            apm = "am" if "a" in end_str else "pm"
        else:
            start_num = int(start_str.split(":")[0])
            apm = "am" if start_num >= 8 else "pm"
        start_time = datetime.strptime(start_str + apm, "%I:%M%p" if ":" in start_str else "%I%p")
        end_dt = None
        if end_str.strip():
            end_str = re.search(r"\d{1,2}(:\d{2})?", end_str).group()
            end_time = datetime.strptime(end_str + apm, "%I:%M%p" if ":" in end_str else "%I%p")
            if end_time < start_time:
                end_time = end_time + timedelta(hours=12)
            end_dt = datetime.combine(dt_obj.date(), end_time.time())
        return datetime.combine(dt_obj.date(), start_time.time()), end_dt
