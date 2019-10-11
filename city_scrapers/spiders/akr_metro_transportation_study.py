import json
import re
from collections import defaultdict
from datetime import datetime

import scrapy
from city_scrapers_core.constants import ADVISORY_COMMITTEE
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider
from dateutil.relativedelta import relativedelta


class AkrMetroTransportationStudySpider(CityScrapersSpider):
    name = "akr_metro_transportation_study"
    agency = "Akron Metropolitan Area Transportation Study"
    timezone = "America/Detroit"
    start_urls = ["http://amatsplanning.org/category/meetings/"]

    def parse(self, response):
        self.month_link_map = self._parse_archive(response)
        this_month = datetime.now().replace(day=1)
        for month in [this_month + relativedelta(months=m) for m in range(-2, 3)]:
            yield scrapy.Request(
                "http://amatsplanning.org/calendar/{}/".format(month.strftime("%Y-%m")),
                callback=self._parse_calendar,
                dont_filter=True,
            )

    def _parse_archive(self, response):
        month_link_map = defaultdict(list)
        for section in response.css(".large-12.archive-subsection"):
            month_match = re.search(
                r"[A-Z][a-z]{2,8} \d{4}",
                section.css("h2::text").extract_first() or ""
            )
            if not month_match:
                continue
            month_year = month_match.group()
            for link in section.css("a"):
                link_title = " ".join(link.css("*::text").extract())
                if "Packet" in link_title:
                    link_title = "Meeting Packet"
                month_link_map[month_year].append({
                    "title": link_title,
                    "href": response.urljoin(link.attrib["href"]),
                })
        return month_link_map

    def _parse_calendar(self, response):
        schema_json = response.css("script[type='application/ld+json']::text").extract()
        if len(schema_json) < 2:
            return
        events = json.loads(schema_json[-1])
        for event in events:
            if "Committee" in event["name"]:
                yield scrapy.Request(event["url"], callback=self._parse_event, dont_filter=True)

    def _parse_event(self, response):
        data = json.loads(response.css("script[type='application/ld+json']::text").extract()[-1])[0]
        start = self._parse_dt(data.get("startDate"))
        if not start:
            return
        meeting = Meeting(
            title=data["name"],
            description="",
            classification=ADVISORY_COMMITTEE,
            start=start,
            end=self._parse_dt(data.get("endDate")),
            all_day=False,
            time_notes="",
            location=self._parse_location(data),
            links=self._parse_links(start, data["name"]),
            source=response.url,
        )

        meeting["status"] = self._get_status(meeting)
        meeting["id"] = self._get_id(meeting)

        yield meeting

    def _parse_dt(self, date_str):
        if not date_str:
            return
        return datetime.strptime(date_str[0:-6], "%Y-%m-%dT%H:%M:%S")

    def _parse_location(self, item):
        """Parse or generate location."""
        if not item.get("location"):
            return {
                "address": "",
                "name": "TBD",
            }

        loc_obj = {
            "name": item["location"]["name"],
            "address": "",
        }
        if item["location"].get("address"):
            loc_obj["address"] = " ".join([
                item["location"]["address"].get(p)
                for p in ["streetAddress", "addressLocality", "addressRegion", "postalCode"]
                if item["location"]["address"].get(p)
            ])
        return loc_obj

    def _parse_links(self, date_obj, title):
        """Parse or generate links."""
        return [
            link for link in self.month_link_map[date_obj.strftime("%B %Y")]
            if title.lower() in link["title"].lower() or "Packet" in link["title"]
        ]
