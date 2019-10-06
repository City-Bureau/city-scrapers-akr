import json
import re
from datetime import datetime

import scrapy
from city_scrapers_core.constants import BOARD
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider
from dateutil.relativedelta import relativedelta


class SummDevelopmentalDisabilitiesSpider(CityScrapersSpider):
    name = "summ_developmental_disabilities"
    agency = "Summit County Developmental Disabilities Board"
    timezone = "America/Detroit"
    allowed_domains = ["www.summitdd.org"]
    custom_settings = {"ROBOTSTXT_OBEY": False, "HTTPERROR_ALLOW_ALL": True}

    def __init__(self, *args, **kwargs):
        self.month_meeting_map = {}
        super().__init__(*args, **kwargs)

    def start_requests(self):
        this_month = datetime.now().replace(day=1)
        for m in range(-3, 3):
            yield scrapy.Request(
                (
                    "http://www.summitdd.org/wp-admin/admin-ajax.php?action=WP_FullCalendar&type=event&event-categories=30&start={}"  # noqa
                ).format((this_month + relativedelta(months=m)).strftime("%Y-%m-%d")),
                callback=self.parse,
                dont_filter=True,
            )

    def parse(self, response):
        """
        `parse` should always `yield` Meeting items.

        Change the `_parse_title`, `_parse_start`, etc methods to fit your scraping
        needs.
        """
        data = json.loads(response.text)
        for item in data:
            yield response.follow(item["url"], callback=self._parse_detail, dont_filter=True)

    def _parse_detail(self, response):
        start = self._parse_start(response)
        if not start:
            return

        meeting = Meeting(
            title="Developmental Disabilities Board",
            description="",
            classification=BOARD,
            start=start,
            end=None,
            all_day=False,
            time_notes="",
            location=self._parse_location(response),
            links=[],
            source=response.url,
        )

        meeting["status"] = self._get_status(meeting)
        meeting["id"] = self._get_id(meeting)

        self.month_meeting_map[(start.year, start.month)] = meeting
        yield response.follow(
            (
                "/about/summit-dd-board/board-meetings/{}-meeting-documents/{}-board-meeting-documents/"  # noqa
            ).format(
                start.year,
                start.strftime("%B").lower(),
            ),
            callback=self._parse_links,
            dont_filter=True,
        )

    def _parse_start(self, response):
        """Parse start datetime as a naive datetime object."""
        dt_str = " ".join(response.css(".large-6 h3 + p")[:1].css("*::text").extract())
        date_match = re.search(r"\d{1,2}\.\d{1,2}\.\d{4}", dt_str)
        if not date_match:
            return
        time_str = "12:00 am"
        time_match = re.search(r"\d{1,2}(:\d{2})? [apm]{2}", dt_str)
        if time_match:
            time_str = time_match.group()
        dt_fmt = "%m.%d.%Y%I:%M %p"
        if ":" not in time_str:
            dt_fmt = "%m.%d.%Y%I %p"
        return datetime.strptime(date_match.group() + time_str, dt_fmt)

    def _parse_location(self, response):
        """Parse or generate location."""
        loc_parts = [
            p.strip() for p in response.css(".location-address::text").extract() if p.strip()
        ]
        if loc_parts[1][0].isdigit():
            return {
                "name": loc_parts[0].replace("\u2013", "-"),
                "address": " ".join(loc_parts[1:]).strip()
            }
        return {"name": "", "address": " ".join(loc_parts)}

    def _parse_links(self, response):
        """Parse or generate links."""
        month_year_match = re.search(r"(?P<year>\d{4}).*(?<=/)(?P<month>[a-z]+)", response.url)
        year_str = month_year_match.group("year")
        month_str = month_year_match.group("month").title()
        date_obj = datetime.strptime(year_str + month_str, "%Y%B").date()

        meeting = self.month_meeting_map.get((date_obj.year, date_obj.month))
        if not meeting:
            return

        for link in response.css(".entry-content a"):
            meeting["links"].append({
                "title": " ".join(link.css("*::text").extract()).strip().replace("\u2013", "-"),
                "href": response.urljoin(link.attrib["href"]),
            })
        yield meeting
