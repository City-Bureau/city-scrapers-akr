from collections import defaultdict
from datetime import datetime

import scrapy
from city_scrapers_core.constants import CITY_COUNCIL
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider
from dateutil.relativedelta import relativedelta


class SummCountyCouncilSpider(CityScrapersSpider):
    name = "summ_county_council"
    agency = "Summit County Council"
    timezone = "America/Detroit"
    location = {
        "name": "Council Chambers",
        "address": "175 S Main St, Floor 7, Akron, OH 44308",
    }

    def __init__(self, *args, **kwargs):
        self.link_map = defaultdict(list)
        super().__init__(*args, **kwargs)

    @property
    def start_urls(self):
        return self.doc_urls[:1]

    @property
    def doc_urls(self):
        this_month = datetime.now().replace(day=1)
        earliest_month = this_month - relativedelta(months=2)
        groups = []
        for year in set([earliest_month.year, this_month.year]):
            groups.extend([
                ("agendas", "committee", year),
                ("minutes", "committee", year),
                ("agendas", "council", year),
                ("minutes", "council", year),
            ])
        return [
            "https://council.summitoh.net/index.php/legislative-information/{}/{}/{}".format(*g)
            for g in groups
        ]

    def parse(self, response):
        """
        `parse` should always `yield` Meeting items.

        Change the `_parse_title`, `_parse_start`, etc methods to fit your scraping
        needs.
        """
        if response.url not in self.doc_urls:
            return

        url_idx = self.doc_urls.index(response.url)
        self._parse_documents(response)
        if url_idx == len(self.doc_urls) - 1:
            yield from self._get_calendar_pages()
        else:

            yield scrapy.Request(self.doc_urls[url_idx + 1], dont_filter=True)

    def _get_calendar_pages(self):
        this_month = datetime.now().replace(day=1)
        months = [this_month + relativedelta(months=i) for i in range(-2, 3)]
        for month in months:
            yield scrapy.Request(
                (
                    "https://council.summitoh.net/phpicalendar/month.php?cal=County_of_Summit_County_Council_Events_Calendar&getdate={}"  # noqa
                ).format(month.strftime("%Y%m%d")),
                callback=self._parse_calendar,
                dont_filter=True,
            )

    def _parse_documents(self, response):
        link_title = "Agenda" if "agenda" in response.url else "Minutes"
        body_type = "Committee" if "committee" in response.url else "Council"
        for link in response.css("td a.jd_download_url"):
            date_str = link.css("*::text").extract_first().split(" ")[0]
            date_obj = datetime.strptime(date_str, "%m-%d-%y").date()
            self.link_map[(body_type, date_obj)].append({
                "title": link_title,
                "href": response.urljoin(link.attrib["href"]),
            })

    def _parse_calendar(self, response):
        year_str = response.url[-8:-4]
        for item in response.css("tr[align='left']"):
            title = self._parse_title(item)
            if not title:
                continue
            start, end = self._parse_start_end(item, year_str)
            meeting = Meeting(
                title=title,
                description="",
                classification=CITY_COUNCIL,
                start=start,
                end=end,
                all_day=False,
                time_notes="",
                location=self.location,
                links=self._parse_links(title, start),
                source=response.url
            )

            meeting["status"] = self._get_status(meeting, text=" ".join(item.extract()))
            meeting["id"] = self._get_id(meeting)

            yield meeting

    def _parse_title(self, item):
        """Parse or generate meeting title."""
        title_str = item.css("td:nth-child(2) a.psf::text").extract_first().strip()
        if "Council" in title_str:
            return "County Council"
        elif "Committee" in title_str:
            return "Committees"

    def _parse_start_end(self, item, year_str):
        """Parse start, end datetimes as naive datetime objects."""
        date_str = " ".join(item.css("td:first-child a.psf *::text").extract()
                            ).strip().split(", ")[-1]
        time_str = " ".join(item.css("td:first-child span *::text").extract()).strip()
        start_str, end_str = time_str.split(" - ")
        return (
            datetime.strptime(year_str + date_str + start_str, "%Y%b %d%I:%M %p"),
            datetime.strptime(year_str + date_str + end_str, "%Y%b %d%I:%M %p"),
        )

    def _parse_links(self, title, start):
        """Parse or generate links."""
        body_type = "Committee" if "Committee" in title else "Council"
        return self.link_map[(body_type, start.date())]
