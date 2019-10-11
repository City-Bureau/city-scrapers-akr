import re
from collections import defaultdict
from datetime import datetime
from io import BytesIO, StringIO
from zipfile import ZipFile

from city_scrapers_core.constants import BOARD, COMMITTEE
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider
from scrapy import Selector


class SummDevelopmentFinanceSpider(CityScrapersSpider):
    name = "summ_development_finance"
    agency = "Summit County Development Finance Authority"
    timezone = "America/Detroit"
    start_urls = ["http://www.developmentfinanceauthority.org/about/scheduled-meetings/"]
    location = {
        "name": "4th Floor Conference Room 408",
        "address": "47 N Main St, Akron, OH 44308",
    }

    def parse(self, response):
        """
        `parse` should always `yield` Meeting items.

        Change the `_parse_title`, `_parse_start`, etc methods to fit your scraping
        needs.
        """
        self._validate_location(response)
        self.link_date_map = self._parse_link_date_map(response)
        schedule_urls = []
        for link in response.css("section a"):
            link_text = " ".join(link.css("*::text").extract())
            if "Schedule" not in link_text:
                continue
            year_match = re.search(r"\d{4}", link_text)
            if year_match:
                schedule_urls.append((year_match.group(), link.attrib["href"]))

        schedule_url = sorted(schedule_urls, key=lambda s: s[0])[-1][1]
        yield response.follow(schedule_url, callback=self._parse_schedule, dont_filter=True)

    def _parse_schedule(self, response):
        docx_bytes = BytesIO(response.body)
        docx_str = ""
        with ZipFile(docx_bytes) as zf:
            for zip_info in zf.infolist():
                if zip_info.filename == "word/document.xml":
                    with zf.open(zip_info) as docx_file:
                        docx_str = StringIO(docx_file.read().decode())
        if not docx_str:
            return
        year_str = re.findall(r"\d{4}", response.url)[-1]
        # Remove MS Word namespaces on tags to use selectors
        sel = Selector(text=docx_str.getvalue())
        sel.remove_namespaces()
        for row in sel.css("tr"):
            row_str = re.sub(r"\s+", " ", " ".join(row.css("*::text").extract())).strip()
            date_strs = re.findall(r"[a-zA-Z]{3,9} \d{1,2}", row_str)
            for idx, date_str in enumerate(date_strs):
                title = self._parse_title(idx)
                start = self._parse_start(date_str, year_str)
                meeting = Meeting(
                    title=title,
                    description="",
                    classification=self._parse_classification(title),
                    start=start,
                    end=None,
                    all_day=False,
                    time_notes="See source to confirm details",
                    location=self.location,
                    links=self.link_date_map[(title, start.date())],
                    source=self.start_urls[0],
                )

                meeting["status"] = self._get_status(meeting)
                meeting["id"] = self._get_id(meeting)

                yield meeting

    def _parse_link_date_map(self, response):
        link_date_map = defaultdict(list)
        for link in response.css("section a"):
            link_text = re.sub(r"\s+", " ", " ".join(link.css("*::text").extract())).strip()
            date_match = re.search(r"\d{4}-\d{1,2}-\d{1,2}", link.attrib["href"])
            if not date_match:
                continue
            title_str = "Board of Directors"
            if "committee" in link_text.lower() or "committee" in link.attrib["href"].lower():
                title_str = "Executive Committee"
            date_obj = datetime.strptime(date_match.group(), "%Y-%m-%d").date()
            link_date_map[(title_str, date_obj)].append({
                "title": "Agenda" if "agenda" in link_text.lower() else link_text,
                "href": response.urljoin(link.attrib["href"]),
            })
        return link_date_map

    def _parse_title(self, idx):
        """Parse or generate meeting title."""
        if idx == 0:
            return "Board of Directors"
        return "Executive Committee"

    def _parse_classification(self, title):
        """Parse or generate classification from allowed options."""
        if "Board" in title:
            return BOARD
        return COMMITTEE

    def _parse_start(self, date_str, year_str):
        """Parse start datetime as a naive datetime object."""
        return datetime.strptime(" ".join([date_str, year_str, "8:30"]), "%b %d %Y %H:%M")

    def _validate_location(self, response):
        """Parse or generate location."""
        section_str = " ".join(response.css("section *::text").extract())
        if "47 N" not in section_str:
            raise ValueError("Meeting location has changed")
