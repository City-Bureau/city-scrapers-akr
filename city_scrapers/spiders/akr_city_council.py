import re
from datetime import datetime, time, timedelta

from city_scrapers_core.constants import CITY_COUNCIL
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider
from dateutil.parser import parse


class AkrCityCouncilSpider(CityScrapersSpider):
    name = "akr_city_council"
    agency = "Akron City Council - Council"
    timezone = "America/Detroit"
    location = {
        "name": "City Hall",
        "address": "166 South High St Akron, OH 44308",
    }
    meeting_defaults = {
        "title": "Regular council meeting",
        "description": "",
        "end": None,
        "all_day": False,
        "classification": CITY_COUNCIL,
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
            agenda_link = item.css(
                "td:last-child a::attr(href)"
            ).extract_first()  # noqa
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
                            {
                                "title": "Agenda",
                                "href": response.urljoin(pdf_link),
                            }  # noqa
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
                    start=datetime.strptime(start_str, "%m/%d/%Y %I:%M:%S %p"),
                    links=[],
                    source=response.url,
                    **self.meeting_defaults,
                )
                meeting["status"] = self._get_status(meeting)
                meeting["id"] = self._get_id(meeting)
                yield meeting

    def _parse_detail(self, response, **kwargs):
        """Parse both the city council and committee meetings from the agenda page"""  # noqa
        bold_text = " ".join(
            response.css("span[style*='bold']::text").extract()
        )  # noqa
        date_match = re.search(r"[a-zA-Z]{3,10} \d{1,2}, \d{4}", bold_text)
        if not date_match:
            self.logger.error("No date found in the bold text")
            return
        start_date = datetime.strptime(date_match.group(), "%B %d, %Y").date()

        # Target the "regular city council" row in the
        # table to get the meeting time.
        start_time_selector = '//tr[translate(td[last()]/p/span/text(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz") = "regular council meeting"]/td[3]/p/span/text()'  # noqa
        meeting_time_str = response.xpath(start_time_selector).get()
        if not meeting_time_str:
            self.logger.error("No meeting time found - default to midnight")
            meeting_time = time(0, 0)
        else:
            parsed_time = parse(meeting_time_str).time()
            meeting_time = parsed_time

        # Combine date and time into a single datetime object
        meeting_datetime = datetime.combine(start_date, meeting_time)

        # Parse the main city council meeting from the agenda page
        meeting = Meeting(
            start=meeting_datetime,
            links=kwargs.get("links", []),
            source=response.url,
            **self.meeting_defaults,
        )
        meeting["status"] = self._get_status(meeting)
        meeting["id"] = self._get_id(meeting)
        yield meeting
