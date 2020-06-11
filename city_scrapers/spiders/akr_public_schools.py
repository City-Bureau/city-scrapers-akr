import re
from datetime import datetime

from city_scrapers_core.constants import BOARD, COMMITTEE
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider
from scrapy import Selector


class AkrPublicSchoolsSpider(CityScrapersSpider):
    name = "akr_public_schools"
    agency = "Akron Public Schools"
    timezone = "America/Detroit"
    start_urls = ["https://go.boarddocs.com/oh/akron/Board.nsf/XML-ActiveMeetings"]
    location = {
        "name": "Sylvester Small Administration Building",
        "address": "10 N Main St, Akron, OH 44308",
    }

    def parse(self, response):
        """
        `parse` should always `yield` Meeting items.

        Change the `_parse_title`, `_parse_start`, etc methods to fit your scraping
        needs.
        """
        # Getting around broken XML response by breaking into chunks
        meetings_split = (
            response.text.split("<meetings>")[1]
            .split("</meetings>")[0]
            .split("</meeting>")
        )
        meeting_items = [
            Selector(text=m + "</meeting>").xpath("//meeting") for m in meetings_split
        ]
        filtered_meetings = [
            m
            for m in meeting_items
            if m.xpath("start/date/text()").extract_first()
            and "Archive" not in (m.xpath("description/text()").extract_first() or "")
        ]
        for idx, item in enumerate(
            sorted(
                filtered_meetings,
                key=lambda m: m.xpath("start/date/text()").extract_first(),
                reverse=True,
            )
        ):
            if idx == 0:
                yield from self._yield_next_meeting(item)
            self._validate_location(item)
            start = self._parse_start(item)
            if not start:
                continue
            title = self._parse_title(item)
            source = self._parse_source(item)
            meeting = Meeting(
                title=title,
                description="",
                classification=self._parse_classification(title),
                start=start,
                end=None,
                time_notes="",
                all_day=False,
                location=self.location,
                links=self._parse_links(source),
                source=source or "https://go.boarddocs.com/oh/akron/Board.nsf/Public",
            )
            meeting["status"] = self._get_status(
                meeting, text=item.xpath("description/text()").extract_first() or ""
            )
            meeting["id"] = self._get_id(meeting)
            yield meeting

    def _yield_next_meeting(self, item):
        """Parse next meeting if available"""
        dt_matches = re.findall(
            r"[A-Z][a-z]{2,8} \d{1,2}, \d{4}, at \d{1,2}:\d{2} [apm\.]{2,4}",
            item.xpath("description/text()").extract_first(),
        )
        if len(dt_matches) > 1:
            for dt_str in dt_matches[1:]:
                meeting = Meeting(
                    title="Board of Education",
                    description="",
                    classification=BOARD,
                    start=datetime.strptime(
                        dt_str.replace(".", ""), "%B %d, %Y, at %I:%M %p"
                    ),
                    end=None,
                    time_notes="",
                    all_day=False,
                    location=self.location,
                    links=[],
                    source="https://go.boarddocs.com/oh/akron/Board.nsf/Public",
                )
                meeting["status"] = self._get_status(meeting)
                meeting["id"] = self._get_id(meeting)
                yield meeting

    def _parse_title(self, item):
        """Parse or generate meeting title."""
        title_str = item.xpath("name/text()").extract_first()
        if "board" in title_str.lower():
            return "Board of Education"
        return re.split(r"\s+at\s+\d", title_str)[0].replace("Meeting", "").strip()

    def _parse_classification(self, title):
        """Parse or generate classification from allowed options."""
        if "Board" in title:
            return BOARD
        return COMMITTEE

    def _parse_start(self, item):
        """Parse start datetime as a naive datetime object."""
        date_str = (item.xpath("start/date/text()").extract_first() or "").strip()
        if not date_str:
            return
        desc = item.xpath("description/text()").extract_first() or ""
        time_match = re.search(r"\d{1,2}:\d{2} [apmAPM\.]{2,4}", desc)
        time_str = "12:00 am"
        if time_match:
            time_str = time_match.group().replace(".", "").lower()
        return datetime.strptime(date_str + time_str, "%Y-%m-%d%I:%M %p")

    def _validate_location(self, item):
        """Parse or generate location."""
        if "Main St" not in item.xpath("description/text()").extract_first():
            raise ValueError("Meeting location has changed")

    def _parse_links(self, source):
        """Parse or generate links."""
        links = []
        if source:
            links.append({"title": "Agenda", "href": source})
        return links

    def _parse_source(self, item):
        """Parse or generate source."""
        link_match = re.search(r"(?<=\<link\>).*?(?=[\<\n\s])", item.extract()[0])
        if link_match:
            return link_match.group()
