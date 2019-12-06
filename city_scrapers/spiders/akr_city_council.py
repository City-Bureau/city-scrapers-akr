import re
from datetime import datetime, time, timedelta
from itertools import zip_longest

from city_scrapers_core.constants import CITY_COUNCIL
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider


def grouper(n, iterable, fillvalue=None):
    """From itertools recipes"""
    args = [iter(iterable)] * n
    return zip_longest(fillvalue=fillvalue, *args)


class AkrCityCouncilSpider(CityScrapersSpider):
    name = "akr_city_council"
    agency = "Akron City Council"
    timezone = "America/Detroit"
    location = {
        "name": "City Hall",
        "address": "166 South High St Akron, OH 44308",
    }
    meeting_defaults = {
        "description": "",
        "end": None,
        "all_day": False,
        "classification": CITY_COUNCIL,
        "time_notes": "",
        "location": location,
    }

    @property
    def start_urls(self):
        """Filter for meetings within a 60 day window"""
        today = datetime.now()
        start = today - timedelta(days=30)
        end = today + timedelta(days=30)
        return [(
            "https://onlinedocs.akronohio.gov/OnBaseAgendaOnline/Meetings/Search?dropid=11&mtids=101&dropsv={}&dropev={}"  # noqa
        ).format(start.strftime("%m/%d/%Y"), end.strftime("%m/%d/%Y"))]

    def parse(self, response):
        """
        `parse` should always `yield` Meeting items.

        Change the `_parse_title`, `_parse_start`, etc methods to fit your scraping
        needs.
        """
        for item in response.css(".meeting-row"):
            agenda_link = item.css("td:last-child a::attr(href)").extract_first()
            if agenda_link:
                agenda_link = agenda_link.replace(
                    "Meetings/ViewMeeting?i", "Documents/ViewAgenda?meetingI"
                )
                pdf_link = re.sub(
                    r"downloadfile",
                    "ViewDocument",
                    item.css("td:last-child a::attr(href)").extract()[-1],
                    flags=re.I
                )
                yield response.follow(
                    agenda_link,
                    callback=self._parse_detail,
                    cb_kwargs={"links": [{
                        "title": "Agenda",
                        "href": response.urljoin(pdf_link),
                    }]},
                    dont_filter=True
                )
            else:
                start_str = item.css("[data-sortable-type='mtgTime']::text").extract_first().strip()
                meeting = Meeting(
                    title="City Council",
                    start=datetime.strptime(start_str, "%m/%d/%Y %I:%M:%S %p"),
                    links=[],
                    source=response.url,
                    **self.meeting_defaults,
                )
                meeting["status"] = self._get_status(meeting)
                meeting["id"] = self._get_id(meeting)

                yield meeting

    def _parse_detail(self, response, **kwargs):
        """Parse both the city council and committee meetings from the agenda page"""
        bold_text = " ".join(response.css("span[style*='bold']::text").extract())
        date_match = re.search(r"[a-zA-Z]{3,10} \d{1,2}, \d{4}", bold_text)
        if not date_match:
            return
        start_date = datetime.strptime(date_match.group(), "%B %d, %Y").date()
        yield from self._parse_city_council_meeting(response, start_date, **kwargs)
        yield from self._parse_committee_meetings(response, start_date)

    def _parse_city_council_meeting(self, response, start_date, **kwargs):
        """Parse the main city council meeting from the agenda page"""
        meeting = Meeting(
            title="City Council",
            start=datetime.combine(start_date, time(19)),
            links=kwargs.get("links", []),
            source=response.url,
            **self.meeting_defaults,
        )

        meeting["status"] = self._get_status(meeting)
        meeting["id"] = self._get_id(meeting)
        yield meeting

    def _parse_committee_meetings(self, response, start_date):
        """Parse committee meetings from cells without strikethrough"""
        committee_cells = response.css("table[style*='width:49'] td")
        for time_cell, title_cell in grouper(2, committee_cells):
            if len(time_cell.css("[style*='line-through']")) > 0:
                continue
            time_str = re.sub(r"[\.\s]", "", " ".join(time_cell.css("*::text").extract()))
            if not re.search(r"\d{1,2}:\d{1,2}[apmAPM]{2}", time_str):
                continue
            start_time = datetime.strptime(time_str, "%I:%M%p").time()
            title_str = " ".join(title_cell.css("*::text").extract()).strip()
            meeting = Meeting(
                title=title_str + " Committee",
                start=datetime.combine(start_date, start_time),
                links=[],
                source=response.url,
                **self.meeting_defaults,
            )

            meeting["status"] = self._get_status(meeting)
            meeting["id"] = self._get_id(meeting)
            yield meeting
