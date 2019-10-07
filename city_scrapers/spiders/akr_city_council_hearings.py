import json
import re
from datetime import datetime, timedelta

from city_scrapers_core.constants import FORUM
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider


class AkrCityCouncilHearingsSpider(CityScrapersSpider):
    name = "akr_city_council_hearings"
    agency = "Akron City Council"
    timezone = "America/Detroit"
    allowed_domains = ["www.akroncitycouncil.org"]
    start_urls = ["http://www.akroncitycouncil.org/upcoming-meetings/"]
    location = {
        "name": "City Hall, Council Chambers",
        "address": "166 South High St Akron, OH 44308",
    }

    def parse(self, response):
        """
        `parse` should always `yield` Meeting items.

        Change the `_parse_title`, `_parse_start`, etc methods to fit your scraping
        needs.
        """
        script_str = response.css(".events-tray script::text").extract_first()
        data_str = re.search(r"(?<=events = ).*?(?=;)", script_str).group()
        # Only pull meetings a max of 90 days into the future (since most automatically repeat)
        max_dt = datetime.now() + timedelta(days=90)

        for item in json.loads(data_str):
            # Ignore non-meetings or regular City Council/Committee meetings
            if (
                item["location"] == "City of Akron" or "Committee" in item["Name"]
                or "Council" in item["Name"] or "Trick" in item["Name"]
            ):
                continue

            start = self._parse_dt_str(item["startDate"])
            if start > max_dt:
                continue

            meeting = Meeting(
                title=self._parse_title(item),
                description=self._parse_description(item),
                classification=FORUM,
                start=start,
                end=self._parse_dt_str(item["endDate"]),
                all_day=False,
                time_notes="",
                location=self._parse_location(item),
                links=[],
                source=self._parse_source(item, response),
            )

            meeting["status"] = self._get_status(meeting)
            meeting["id"] = self._get_id(meeting)

            yield meeting

    def _parse_title(self, item):
        """Parse or generate meeting title."""
        return re.sub(r"\(\d+\)", "", item["Name"]).strip()

    def _parse_description(self, item):
        """Parse or generate meeting description."""
        return item["summary"]

    def _parse_dt_str(self, dt_str):
        return datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S")

    def _parse_location(self, item):
        """Parse or generate location."""
        # If the location starts with a number, assume it's an address. Otherwise use the text
        # before the first comma as the location name
        if "Council Chambers" in item["location"]:
            return self.location

        split_loc = item["location"].split(", ", 1)
        if item["location"][0].isdigit() or len(split_loc) == 1:
            return {"name": "", "address": item["location"]}
        return {
            "name": split_loc[0],
            "address": split_loc[1],
        }

    def _parse_source(self, item, response):
        """Parse or generate source."""
        return response.urljoin(item["NiceUrl"])
