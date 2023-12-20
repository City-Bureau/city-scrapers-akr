import json
import re
from datetime import datetime, timedelta

from city_scrapers_core.constants import BOARD
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider


class SummSoilWaterConservationSpider(CityScrapersSpider):
    name = "summ_soil_water_conservation"
    agency = "Summit County Soil and Water Conservation District"
    timezone = "America/Detroit"

    @property
    def start_urls(self):
        today = datetime.now()
        last_week = today - timedelta(days=7)
        in_two_months = today + timedelta(days=60)
        return [
            (
                "https://clients6.google.com/calendar/v3/calendars/staffsummitswcd@gmail.com/events"  # noqa
                "?calendarId=staffsummitswcd@gmail.com&singleEvents=true&timeZone=America%2FNew_York&"  # noqa
                "sanitizeHtml=true&timeMin={}T00:00:00-04:00&timeMax={}T00:00:00-04:00&"
                "key=AIzaSyBNlYH01_9Hc5S1J9vuFmu2nUqBZJNAXxs"
            ).format(
                last_week.strftime("%Y-%m-%d"),
                in_two_months.strftime("%Y-%m-%d"),
            )
        ]

    def parse(self, response):
        data = json.loads(response.text)
        for item in data["items"]:
            if "Board" not in item["summary"]:
                continue
            title = self._parse_title(item)
            location = self._parse_location(item)
            if not location:
                continue
            meeting = Meeting(
                title=title,
                description="",
                classification=BOARD,
                start=self._parse_dt(item["start"]["dateTime"]),
                end=self._parse_dt(item["end"]["dateTime"]),
                time_notes="",
                all_day=False,
                location=location,
                links=[],
                source="https://sswcd.summitoh.net/about-us/calendar",
            )
            meeting["status"] = self._get_status(meeting, text=item["status"])
            meeting["id"] = self._get_id(meeting)
            yield meeting

    def _parse_title(self, item):
        return re.sub(r" Meeting$", "", item["summary"].strip())

    def _parse_dt(self, dt_str):
        return datetime.strptime(dt_str[:19], "%Y-%m-%dT%H:%M:%S")

    def _parse_location(self, item):
        if "location" not in item:
            return
        name = ""
        if re.search(r"^\d", item["location"]):
            address = item["location"]
        else:
            split_loc = re.split(r"(?<=[a-z]) ?[,-] (?=\d)", item["location"], 1)
            if len(split_loc) == 1:
                address = split_loc[0]
            else:
                name = split_loc[0].strip()
                address = split_loc[1].strip()
        return {
            "name": name,
            "address": address,
        }
