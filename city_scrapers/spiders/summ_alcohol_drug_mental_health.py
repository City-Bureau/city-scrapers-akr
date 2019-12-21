import json
import re
from collections import defaultdict
from datetime import datetime, timedelta

import pytz
import scrapy
from city_scrapers_core.constants import BOARD, COMMITTEE
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider


class SummAlcoholDrugMentalHealthSpider(CityScrapersSpider):
    name = "summ_alcohol_drug_mental_health"
    agency = "Summit County Alcohol, Drug Addiction and Mental Health Services Board"
    timezone = "America/Detroit"
    start_urls = ["https://www.admboard.org/board-of-directors.aspx"]

    def parse(self, response):
        self.date_link_map = self._parse_documents(response)
        since = datetime.now() - timedelta(days=120)
        since_epoch = str(int(since.timestamp() * 1000))
        yield scrapy.Request(
            "https://tockify.com/api/ngevent?view=agenda&calname=jackstest&start-inclusive=true&longForm=false&showAll=false&search=board&startms="  # noqa
            + since_epoch,
            callback=self._parse_calendar,
            dont_filter=True
        )

    def _parse_documents(self, response):
        date_link_map = defaultdict(list)
        for link in response.css(".modulecontent li a"):
            link_str = " ".join(link.css("*::text").extract())
            date_match = re.search(r"[A-Z][a-z]{2,8},? \d{4}", link_str)
            if not date_match:
                continue
            date_str = date_match.group().replace(",", "")
            date_link_map[date_str].append({
                "title": "Minutes",
                "href": response.urljoin(link.attrib["href"]),
            })
        return date_link_map

    def _parse_calendar(self, response):
        data = json.loads(response.text)
        for item in data["events"]:
            yield scrapy.Request(
                "https://tockify.com/jackstest/detail/{}/{}".format(
                    item["eid"]["uid"], item["eid"]["tid"]
                ),
                callback=self._parse_event,
                dont_filter=True,
            )

    def _parse_event(self, response):
        """
        `_parse_calendar` should always `yield` Meeting items.

        Change the `_parse_title`, `_parse_start`, etc methods to fit your scraping
        needs.
        """
        data = json.loads(response.css("script[type='application/ld+json']::text").extract_first())
        detail = {}
        script_str = " ".join(response.css("head script[type='text/javascript']::text").extract())
        json_match = re.search(r"(?<=window\.tkf = ).*?(?=;\n)", script_str)
        if json_match:
            detail = json.loads(json_match.group())
            events = detail.get("bootdata", {}).get("query", {}).get("detail", {}).get("events", [])
            if len(events) > 0:
                detail = events[0]

        title = self._parse_title(data)
        classification = self._parse_classification(title)
        start = self._parse_dt(data["startDate"])
        links = []
        if classification == BOARD:
            links = self.date_link_map[start.strftime("%B %Y")]
        meeting = Meeting(
            title=title,
            description="",
            classification=classification,
            start=start,
            end=self._parse_dt(data["endDate"]),
            all_day=False,
            time_notes="",
            location=self._parse_location(detail),
            links=links + self._parse_links(detail),
            source=response.url,
        )

        meeting["status"] = self._get_status(meeting, text=data["name"])
        meeting["id"] = self._get_id(meeting)

        yield meeting

    def _parse_title(self, item):
        """Parse or generate meeting title."""
        if "Regular" in item["name"]:
            return "Board of Directors"
        if "Committee" in item["name"]:
            title_str = re.search(r".*?Committee", item["name"]).group()
            return re.sub(r"Board of Directors(\')?\s+", "", title_str).replace("ad hoc",
                                                                                "Ad Hoc").strip()
        return re.sub(r"postpone(\w+)\s+-?\s+", "", item["name"], flags=re.I).strip()

    def _parse_classification(self, title):
        """Parse or generate classification from allowed options."""
        if "Committee" in title:
            return COMMITTEE
        return BOARD

    def _parse_dt(self, dt_str):
        """Parse datetime string in UTC and convert it to a naive datetime in local time"""
        dt = datetime.strptime(dt_str.replace(":", ""), "%Y-%m-%dT%H%M%S%z")
        tz = pytz.timezone(self.timezone)
        return dt.astimezone(tz).replace(tzinfo=None)

    def _parse_location(self, detail):
        """Parse or generate location."""
        return {
            "name": detail["content"].get("place", ""),
            "address": detail["content"].get("address", ""),
        }

    def _parse_links(self, detail):
        """Parse or generate links."""
        links = []
        desc_str = detail["content"]["description"].get("text", "")
        desc_el = scrapy.Selector(text=desc_str)
        for link in desc_el.css("a"):
            link_title = " ".join(link.css("*::text").extract()).strip()
            link_href = link.attrib["href"]
            if "mailto" in link_href:
                continue
            if "agenda" in link_href.lower():
                link_title = "Agenda"
            elif "notice" in link_href.lower():
                link_title = "Notice"
            else:
                link_title = "Materials"
            links.append({
                "title": link_title,
                "href": link_href,
            })
        return links
