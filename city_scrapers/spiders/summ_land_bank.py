import re
from collections import defaultdict
from datetime import datetime
from io import BytesIO, StringIO

from city_scrapers_core.constants import BOARD
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider
from pdfminer.high_level import extract_text_to_fp
from pdfminer.layout import LAParams


class SummLandBankSpider(CityScrapersSpider):
    name = "summ_land_bank"
    agency = "Summit County Land Bank"
    timezone = "America/Detroit"
    start_urls = ["http://www.summitlandbank.org/board-meeting-minutes"]
    location = {
        "name": "Ohio Building, Council Chambers",
        "address": "175 S Main St, Akron, OH 44308",
    }

    def __init__(self, *args, **kwargs):
        self.link_date_map = defaultdict(list)
        super().__init__(*args, **kwargs)

    def parse(self, response):
        """
        `parse` should always `yield` Meeting items.

        Change the `_parse_title`, `_parse_start`, etc methods to fit your scraping
        needs.
        """
        self._parse_documents(response)
        if "minutes" in response.url.lower():
            yield response.follow("/board-meeting-agendas", callback=self.parse)
        else:
            yield response.follow(
                "/board-meeting-notices", callback=self._parse_notice_page
            )

    def _parse_documents(self, response):
        """Parse documents pages, adding to link_date_map"""
        page_title = " ".join(response.css("h2 *::text").extract())
        if "minutes" in page_title.lower():
            link_title = "Minutes"
        else:
            link_title = "Agenda"
        for link in response.css("main .sqs-block-content a"):
            link_str = re.sub(r"\s+", " ", " ".join(link.css("*::text").extract()))
            date_match = re.search(r"[A-Z][a-z]{2,8} \d{1,2},? \d{4}", link_str)
            if not date_match:
                continue
            date_obj = datetime.strptime(
                date_match.group().replace(",", ""), "%B %d %Y"
            ).date()
            self.link_date_map[date_obj].append(
                {"title": link_title, "href": response.urljoin(link.attrib["href"])}
            )

    def _parse_notice_page(self, response):
        """Parse meetings from text or notice pages (if available)"""
        for item in response.css(".horizontalrule-block + .html-block p"):
            item_str = " ".join(item.css("*::text").extract())
            if len(item.css("a")):
                link = item.css("a")[0]
                yield response.follow(
                    link.attrib["href"],
                    callback=self._parse_notice,
                    dont_filter=True,
                    meta={"meeting_text": item_str, "source": response.url},
                )
            else:
                yield self._parse_meeting_text(item_str, response.url)

    def _parse_notice(self, response):
        """
        Parse meeting from notice text if embedded text, otherwise use text in meta
        """
        lp = LAParams(line_margin=0.1)
        out_str = StringIO()
        extract_text_to_fp(BytesIO(response.body), out_str, laparams=lp)
        pdf_text = out_str.getvalue()
        if not pdf_text.strip():
            yield self._parse_meeting_text(response.meta["meeting_text"], response.url)
        else:
            date_match = re.search(
                r"[A-Z][a-z]{2,8} \d{1,2},? \d{4}", response.meta["meeting_text"]
            )
            if date_match:
                date_obj = datetime.strptime(
                    date_match.group().replace(",", ""), "%B %d %Y"
                ).date()
                if "Notice" not in [
                    link["title"] for link in self.link_date_map[date_obj]
                ]:
                    self.link_date_map[date_obj].append(
                        {"title": "Notice", "href": response.url}
                    )
            yield self._parse_meeting_text(
                re.sub(r"\s+", " ", pdf_text), response.meta["source"]
            )

    def _parse_meeting_text(self, meeting_text, source):
        start = self._parse_start(meeting_text)
        if not start:
            return

        meeting = Meeting(
            title=self._parse_title(meeting_text),
            description="",
            classification=BOARD,
            start=start,
            end=None,
            all_day=False,
            time_notes="Confirm details in source",
            location=self._parse_location(meeting_text),
            links=self.link_date_map[start.date()],
            source=source,
        )

        meeting["status"] = self._get_status(meeting, text=meeting_text)
        meeting["id"] = self._get_id(meeting)

        return meeting

    def _parse_title(self, item_str):
        """Parse or generate meeting title."""
        if "Special" in item_str:
            return "Board of Directors Special Meeting"
        if "Annual" in item_str:
            return "Annual Board of Directors Meeting"
        if "Retreat" in item_str:
            return "Board of Directors Meeting and Retreat"
        return "Board of Directors"

    def _parse_start(self, item_str):
        """Parse start datetime as a naive datetime object."""
        date_match = re.search(r"[A-Z][a-z]{2,8} \d{1,2},? \d{4}", item_str)
        if not date_match:
            return
        time_match = re.search(r"\d{1,2}(\:\d{2})? ?[apmAPM\.]{2,4}", item_str)
        time_str = "2:00pm"
        if time_match:
            time_str = re.sub(r"(\s+|\.)", "", time_match.group()).lower()
        dt_fmt = "%B %d %Y %I%p"
        if ":" in time_str:
            dt_fmt = "%B %d %Y %I:%M%p"
        return datetime.strptime(
            " ".join([date_match.group().replace(",", ""), time_str]), dt_fmt
        )

    def _parse_location(self, item_str):
        """Parse or generate location."""
        loc_match = re.search(r"(?<= )[0-9]{2,5} [A-Za-z0-9,\. ]+ \d{5}", item_str)
        if "175" in item_str or not loc_match:
            return self.location
        return {
            "name": "",
            "address": re.sub(r"Ohio(?= \d)", "OH", loc_match.group()),
        }
