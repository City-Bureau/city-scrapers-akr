import re
from collections import defaultdict
from datetime import datetime

import scrapy
from city_scrapers_core.constants import BOARD, COMMITTEE
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider


class AkrUniversitySpider(CityScrapersSpider):
    name = "akr_university"
    agency = "University of Akron"
    timezone = "America/Detroit"
    location = {
        "name": "University of Akron Student Union",
        "address": "303 Carroll St, Akron, OH 44304",
    }

    @property
    def start_urls(self):
        return [
            "https://www.uakron.edu/bot/board-memos.dot?folderPath=/bot/docs/"
            + str(datetime.now().year)
        ]

    def parse(self, response):
        self.link_date_map = self._parse_docs(response)
        yield scrapy.Request(
            "https://www.uakron.edu/bot/meetings.dot",
            callback=self._parse_schedule,
            dont_filter=True,
        )

    def _parse_docs(self, response):
        """Parse past Board materials by date"""
        link_date_map = defaultdict(list)
        for link in response.css(".table-striped td a"):
            link_str = " ".join(link.css("*::text").extract())
            date_match = re.search(r"[A-Z][a-z]{2,8} \d{1,2} \d{4}", link_str)
            if not date_match:
                continue
            try:
                date_obj = datetime.strptime(date_match.group(), "%B %d %Y").date()
            except ValueError:
                date_obj = datetime.strptime(date_match.group(), "%b %d %Y").date()
            link_date_map[date_obj].append(
                {"title": "Materials", "href": response.urljoin(link.attrib["href"])}
            )
        return link_date_map

    def _parse_schedule(self, response):
        """
        `parse` should always `yield` Meeting items.

        Change the `_parse_title`, `_parse_start`, etc methods to fit your scraping
        needs.
        """
        for item in response.css(".slim-item ul li"):
            title = self._parse_title(item)
            start = self._parse_start(item)
            if not start:
                continue

            classification = self._parse_classification(title)
            links = []
            if classification == BOARD:
                links = self.link_date_map[start.date()] + [
                    {
                        "title": "Livestream",
                        "href": "https://learn.uakron.edu/video/bot/",
                    }
                ]

            meeting = Meeting(
                title=title,
                description="",
                classification=classification,
                start=start,
                end=None,
                all_day=False,
                time_notes="",
                location=self._parse_location(item),
                links=links,
                source=response.url,
            )

            meeting["status"] = self._get_status(
                meeting, text=" ".join(item.css("*::text").extract())
            )
            meeting["id"] = self._get_id(meeting)

            yield meeting

    def _parse_title(self, item):
        """Parse or generate meeting title."""
        title_str = item.css("strong::text").extract_first()
        if not title_str:
            return "Board of Trustees"
        return title_str.replace(":", "").strip()

    def _parse_classification(self, title):
        """Parse or generate classification from allowed options."""
        if "Board" in title:
            return BOARD
        return COMMITTEE

    def _parse_start(self, item):
        """Parse start datetime as a naive datetime object."""
        item_str = re.sub(r"\s+", " ", " ".join(item.css("*::text").extract())).strip()
        if len(item.css("strong")) > 0:
            # Parse from committee
            year_str = str(datetime.now().year)
            date_match = re.search(r"[A-Z][a-z]{2,8} \d{1,2}", item_str)
            if not date_match:
                return
            date_str = date_match.group()
            time_str = "12:00 am"
            time_match = re.search(r"\d{1,2}:\d{2} [apm\.]{4}", item_str)
            if time_match:
                time_str = time_match.group().replace(".", "")
            return datetime.strptime(year_str + date_str + time_str, "%Y%B %d%I:%M %p")
        else:
            dt_match = re.search(
                r"[A-Z][a-z]{2,8}\.? \d{1,2}, \d{4}, \d{1,2}:\d{2} [apm\.]{4}",
                item_str,
            )
            if not dt_match:
                return
            dt_str = dt_match.group()
            if ". " in dt_str:
                dt_fmt = "%b %d, %Y, %I:%M %p"
            else:
                dt_fmt = "%B %d, %Y, %I:%M %p"
            return datetime.strptime(dt_str.replace(".", ""), dt_fmt)

    def _parse_location(self, item):
        """Parse or generate location."""
        item_str = " ".join(item.css("*::text").extract())
        if len(item.css("strong")) > 0:
            # Return default for committee
            return self.location
        else:
            if "Student Union" in item_str:
                return self.location
            return {
                "name": ", ".join(item_str.split(", ")[3:]).strip(),
                "address": "",
            }
