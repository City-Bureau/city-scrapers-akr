import re
from datetime import datetime

from city_scrapers_core.constants import FORUM
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider


class AkrDowntownPartnershipSpider(CityScrapersSpider):
    name = "akr_downtown_partnership"
    agency = "Downtown Akron Partnership"
    timezone = "America/Detroit"
    start_urls = ["https://www.downtownakron.com/work/district-meetings"]

    def parse(self, response):
        """
        `parse` should always `yield` Meeting items.

        Change the `_parse_title`, `_parse_start`, etc methods to fit your scraping
        needs.
        """
        # Store year in iteration for dates without years
        year_str = ""
        for item in response.css(".max-content-width > p"):
            item_str = " ".join(item.css("strong *::text").extract()).strip()
            if not item_str:
                continue

            title = self._parse_title(item_str)
            for date_str in item.css("*::text").extract()[1:]:
                start = self._parse_start(item_str, date_str, year_str)
                if not start:
                    continue
                year_str = str(start.year)
                meeting = Meeting(
                    title=title,
                    description="",
                    classification=FORUM,
                    start=start,
                    end=None,
                    all_day=False,
                    time_notes="See source to confirm details",
                    location=self._parse_location(item_str, date_str),
                    links=[],
                    source=response.url,
                )

                meeting["status"] = self._get_status(meeting)
                meeting["id"] = self._get_id(meeting)

                yield meeting

    def _parse_title(self, item_str):
        """Parse or generate meeting title."""
        if "Main Street" in item_str:
            return "Main Street"
        return item_str.split(", ")[0].strip()

    def _parse_start(self, item_str, item_date_str, year_str):
        """Parse start datetime as a naive datetime object."""
        time_str = "12:00 am"
        time_match = re.search(r"\d{1,2}(:\d{2})? [apm\.]{2,4}", item_str)
        if time_match:
            time_str = time_match.group().replace(".", "")
        date_match = re.search(r"[A-Z][a-z]{2,8} \d{1,2},? \d{4}", item_date_str)
        if date_match:
            date_str = date_match.group().replace(",", "")
        else:
            date_match = re.search(r"[A-Z][a-z]{2,8} \d{1,2}", item_date_str)
            if not date_match:
                return
            date_str = "{} {}".format(date_match.group(), year_str)
        time_match = re.search(r"\d{1,2}(:\d{2})? [apm\.]{2,4}", item_date_str)
        if time_match:
            time_str = time_match.group().replace(".", "")
        if ":" in time_str:
            time_fmt = "%I:%M %p"
        else:
            time_fmt = "%I %p"
        return datetime.strptime(date_str + time_str, "%B %d %Y" + time_fmt)

    def _parse_location(self, item_str, date_str):
        """Parse or generate location."""
        location = self._parse_location_str(date_str)
        if location["name"] == "TBD":
            location = self._parse_location_str(item_str)
        return location

    def _parse_location_str(self, loc_str):
        if "Jilly" in loc_str:
            return {
                "name": "Jilly's Music Room",
                "address": "111 N Main St, Akron, OH 44308",
            }
        if "Barley House" in loc_str:
            return {
                "name": "Barley House",
                "address": "222 Main St, Akron, OH 44308",
            }
        if "Library" in loc_str:
            return {
                "name": "Akron Summit County Public Library",
                "address": "60 S High St, Akron, OH 44326",
            }
        return {
            "name": "TBD",
            "address": "",
        }
