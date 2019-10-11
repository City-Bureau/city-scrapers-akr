import re
from datetime import datetime, timedelta

from city_scrapers_core.constants import COMMISSION
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider


class SummOpiateTaskForceSpider(CityScrapersSpider):
    name = "summ_opiate_task_force"
    agency = "Summit County Opiate and Addiction Task Force"
    timezone = "America/Detroit"
    start_urls = ["https://www.summitcountyaddictionhelp.org/opiate-task-force-members.aspx"]
    location = {
        "name": "Summit County Public Health Department Auditorium",
        "address": "1867 W Market Street, Akron, OH 44313",
    }

    def parse(self, response):
        """
        `parse` should always `yield` Meeting items.

        Change the `_parse_title`, `_parse_start`, etc methods to fit your scraping
        needs.
        """
        description = " ".join(response.css("h2 + p")[:1].css("*::text").extract())
        self._validate_location(description)
        self._validate_start_time(description)

        for item in response.css("h2 ~ table h4"):
            start = self._parse_start(item)
            if not start:
                continue
            meeting = Meeting(
                title="Key Stakeholders Quarterly Meeting",
                description="",
                classification=COMMISSION,
                start=start,
                end=start + timedelta(hours=1, minutes=30),
                all_day=False,
                time_notes="",
                location=self.location,
                links=self._parse_links(item, response),
                source=response.url,
            )

            meeting["status"] = self._get_status(meeting)
            meeting["id"] = self._get_id(meeting)

            yield meeting

    def _parse_start(self, item):
        """Parse start datetime as a naive datetime object."""
        item_str = " ".join(item.css("*::text").extract())
        date_match = re.search(r"[A-Z][a-z]{2,8} \d{1,2},? \d{4}", item_str)
        if not date_match:
            return
        return datetime.strptime(date_match.group().replace(",", "") + "16", "%B %d %Y%H")

    def _validate_location(self, description):
        if "1867" not in description:
            raise ValueError("Meeting location has changed")

    def _validate_start_time(self, description):
        if "4:00" not in description:
            raise ValueError("Meeting time has changed")

    def _parse_links(self, item, response):
        """Parse or generate links."""
        links = []
        for link in item.css("a"):
            link_title = "Agenda" if "agenda" in link.attrib["href"].lower() else "Minutes"
            links.append({
                "title": link_title,
                "href": response.urljoin(link.attrib["href"]),
            })
        return links
