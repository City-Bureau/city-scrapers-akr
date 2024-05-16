import re
from datetime import datetime, time, timedelta
from itertools import zip_longest

from city_scrapers_core.constants import COMMITTEE
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider


def grouper(n, iterable, fillvalue=None):
    """From itertools recipes"""
    args = [iter(iterable)] * n
    return zip_longest(fillvalue=fillvalue, *args)


class AkrCityCouncilCommitteesSpider(CityScrapersSpider):
    name = "akr_city_council_committees"
    agency = "Akron City Council - Committees"
    timezone = "America/Detroit"
    location = {
        "name": "City Hall",
        "address": "166 South High St Akron, OH 44308",
    }
    meeting_defaults = {
        "title": "Committee meeting",
        "all_day": False,
        "classification": COMMITTEE,
        "time_notes": "",
        "location": location,
    }

    @property
    def start_urls(self):
        today = datetime.now()
        start = today - timedelta(days=30)
        end = today + timedelta(days=90)
        return [
            (
                "https://onlinedocs.akronohio.gov/OnBaseAgendaOnline/Meetings/Search?dropid=11&mtids=101&dropsv={}&dropev={}"  # noqa
            ).format(start.strftime("%m/%d/%Y"), end.strftime("%m/%d/%Y"))
        ]

    def parse(self, response):
        """
        Parse agenda links from the main page and then parse
        the details from each agenda page
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
                    flags=re.I,
                )
                yield response.follow(
                    agenda_link,
                    callback=self._parse_detail,
                    cb_kwargs={
                        "links": [
                            {"title": "Agenda", "href": response.urljoin(pdf_link)}
                        ]
                    },
                    dont_filter=True,
                )
            else:
                start_str = (
                    item.css("[data-sortable-type='mtgTime']::text")
                    .extract_first()
                    .strip()
                )
                meeting = Meeting(
                    **self.meeting_defaults,
                    description="",
                    start=datetime.strptime(start_str, "%m/%d/%Y %I:%M:%S %p"),
                    end=None,
                    links=[],
                    source=response.url,
                )
                meeting["status"] = self._get_status(meeting)
                meeting["id"] = self._get_id(meeting)

                yield meeting

    def _parse_detail(self, response, **kwargs):
        """Parse committee meetings from the agenda page"""
        bold_text = " ".join(response.css("span[style*='bold']::text").extract())
        date_match = re.search(r"[a-zA-Z]{3,10} \d{1,2}, \d{4}", bold_text)
        if not date_match:
            return
        start_date = datetime.strptime(date_match.group(), "%B %d, %Y").date()

        # Get committee cells
        committee_cells = response.css("table[style*='width:49'] td")
        description = ""
        for time_cell, title_cell in grouper(2, committee_cells):
            if len(time_cell.css("[style*='line-through']")) > 0:
                continue
            time_str = re.sub(
                r"[\.\s]", "", " ".join(time_cell.css("*::text").extract())
            )
            if not re.search(r"\d{1,2}:\d{1,2}[apmAPM]{2}", time_str):
                continue
            start_time = datetime.strptime(time_str, "%I:%M%p").time()
            title_str = " ".join(title_cell.css("*::text").extract()).strip()
            description = description + f"{title_str} – {start_time}\n"
        meeting = Meeting(
            **self.meeting_defaults,
            description=description,
            start=datetime.combine(start_date, time(13)),
            end=datetime.combine(start_date, time(17)),
            links=kwargs.get("links", []),
            source=response.url,
        )

        meeting["status"] = self._get_status(meeting)
        meeting["id"] = self._get_id(meeting)
        yield meeting
