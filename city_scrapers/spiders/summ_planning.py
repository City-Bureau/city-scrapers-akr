import math
import re
from collections import defaultdict
from datetime import datetime
from io import BytesIO, StringIO

from city_scrapers_core.constants import COMMISSION
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider
from pdfminer.high_level import extract_text_to_fp
from pdfminer.layout import LAParams
from scrapy import Selector


class SummPlanningSpider(CityScrapersSpider):
    name = "summ_planning"
    agency = "Summit County Planning Commission"
    timezone = "America/Detroit"
    allowed_domains = ["co.summitoh.net"]
    start_urls = [
        "https://co.summitoh.net/index.php/departments/community-a-economic-development/planning"
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    location = {
        "name": "County Council Chambers",
        "address": "175 S Main St, Akron, OH 44308",
    }

    def parse(self, response):
        """Parse links page and then parse PDF"""
        section = self._parse_section(response)
        self.link_date_map = self._parse_links_page(section, response)
        for link in section.css("a"):
            link_text = " ".join(link.css("*::text").extract())
            if "Dates" in link_text:
                yield response.follow(
                    link.attrib["href"], callback=self._parse_pdf_schedule, dont_filter=True
                )
                break

    def _parse_section(self, response):
        """Get the first portion of the accordion section as a Selector"""
        accordion_el = " ".join(response.css(".modulebrd > div > div > div > *").extract())
        split_accordion = re.split(r"\<h3.*?/h3\>", accordion_el)
        return Selector(text=split_accordion[1])

    def _parse_pdf_schedule(self, response):
        """
        `_parse_pdf_schedule` should always `yield` Meeting items.

        Change the `_parse_title`, `_parse_start`, etc methods to fit your scraping
        needs.
        """
        lp = LAParams(line_margin=0.1)
        out_str = StringIO()
        extract_text_to_fp(BytesIO(response.body), out_str, laparams=lp)
        pdf_text = out_str.getvalue()
        all_date_strs = re.findall(r"[A-Z][a-z]{2,8} \d{1,2}, \d{4}", pdf_text)
        # Get first half of the date strings, because these are the meeting dates
        date_strs = all_date_strs[:math.floor(len(all_date_strs) / 2)]
        time_strs = re.findall(r"\d{1,2}:\d{2} [apm\.]{2,4}", pdf_text)
        time_str = time_strs[-1].replace(".", "")

        for date_str in date_strs:
            start = self._parse_start(date_str + time_str)
            meeting = Meeting(
                title="Planning Commission",
                description="",
                classification=COMMISSION,
                start=start,
                end=None,
                all_day=False,
                time_notes="",
                location=self.location,
                links=self.link_date_map[start.date()],
                source=self.start_urls[0],
            )

            meeting["status"] = self._get_status(meeting)
            meeting["id"] = self._get_id(meeting)

            yield meeting

    def _parse_links_page(self, section, response):
        links_date_map = defaultdict(list)
        start_date = None
        for item in section.css("body > *"):
            item_str = " ".join(item.css("*::text").extract()).strip()
            date_match = re.search(r"[A-Z][a-z]{2,8} \d{1,2},? \d{4}", item_str)
            link_title = item_str
            if date_match:
                link_title = "Meeting Packet"
                start_date = datetime.strptime(
                    date_match.group().replace(",", ""),
                    "%B %d %Y",
                ).date()
            if len(item.css("a")) == 0:
                continue
            link_href = response.urljoin(item.css("a::attr(href)").extract_first())
            links_date_map[start_date].append({
                "title": link_title,
                "href": link_href,
            })
        return links_date_map

    def _parse_start(self, dt_str):
        """Parse start datetime as a naive datetime object."""
        return datetime.strptime(dt_str, "%B %d, %Y%I:%M %p")

    def _validate_location(self, text):
        """Validate that location is present in text or raise an error."""
        if "Chambers" not in text:
            raise ValueError("Meeting location has changed")
