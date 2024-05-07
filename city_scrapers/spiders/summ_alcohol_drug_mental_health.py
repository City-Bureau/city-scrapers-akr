import json

from city_scrapers_core.constants import BOARD
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider
from dateutil.parser import parse
from w3lib.html import remove_tags


class SummAlcoholDrugMentalHealthSpider(CityScrapersSpider):
    name = "summ_alcohol_drug_mental_health"
    agency = "Summit County Alcohol, Drug Addiction and Mental Health Services Board"
    timezone = "America/Detroit"
    start_urls = ["https://admboard.org/board-of-directors/"]

    def parse(self, response):
        # Extract JSON-LD script content
        json_ld_scripts = response.xpath('//script[@type="application/ld+json"]/text()')
        for json_ld in json_ld_scripts:
            json_ld_content = json_ld.extract()
            data = json.loads(json_ld_content)
            if data["@type"] == "Event":
                yield from self.parse_event(data)

    def parse_event(self, data):
        title = data["name"]
        description = remove_tags(data.get("description", ""))
        start = self.parse_datetime(data["startDate"])
        end = self.parse_datetime(data["endDate"])
        location = self.parse_location(data)
        links = [{"title": "Event Details", "href": data["url"]}]

        meeting = Meeting(
            title=title,
            description=description,
            classification=BOARD,
            start=start,
            end=end,
            all_day=False,
            time_notes="",
            location=location,
            links=links,
            source=data["url"],
        )
        meeting["status"] = self._get_status(meeting, text=data["eventStatus"])
        meeting["id"] = self._get_id(meeting)
        yield meeting

    def parse_datetime(self, dt_str):
        # Use dateutil's parse to automatically handle different datetime formats
        return parse(dt_str).replace(tzinfo=None)

    def parse_location(self, data):
        location_info = data.get("location", [{}])[0]
        if not location_info:
            return {
                "name": "TBD",
                "address": "",
            }
        return {
            "name": location_info.get("name", ""),
            "address": location_info.get("address", {}).get("streetAddress", ""),
        }
