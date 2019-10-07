import re
from collections import defaultdict
from datetime import datetime

from city_scrapers_core.constants import BOARD, COMMITTEE
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider
from dateutil.relativedelta import relativedelta
from scrapy import FormRequest


class SummChildrenServicesSpider(CityScrapersSpider):
    name = "summ_children_services"
    agency = "Summit County Children Services"
    timezone = "America/Detroit"
    allowed_domains = ["www.summitkids.org"]
    start_urls = ["https://www.summitkids.org/About/Board-of-Trustees/Board-Resolutions-Minutes"]
    location = {
        "name": "Summit County Children Services",
        "address": "264 S Arlington St, Akron, OH 44306",
    }

    def parse(self, response):
        """
        `parse` should always `yield` Meeting items.

        Change the `_parse_title`, `_parse_start`, etc methods to fit your scraping
        needs.
        """
        self.link_date_map = self._parse_documents(response)
        yield response.follow(
            "/Community-Action/Calendar", callback=self._parse_calendar, dont_filter=True
        )

    def _parse_documents(self, response):
        link_date_map = defaultdict(list)
        for link in response.css(".accordion a"):
            link_text = " ".join(link.css("*::text").extract())
            month_year_match = re.search(r"[A-Z][a-z]{2,8} \d{4}", link_text)
            if month_year_match:
                link_title = link_text.strip()
                if "Minutes" in link_title:
                    link_title = "Minutes"
                if "Resolutions" in link_title:
                    link_title = "Resolutions"
                link_date_map[month_year_match.group()].append({
                    "title": link_title,
                    "href": response.urljoin(link.attrib["href"]),
                })
        return link_date_map

    def _parse_calendar(self, response):
        """
        The __EVENTARGUMENT changes by the number of days to offset from an arbitrary number.
        Here we're getting the start value and using it to calculate the value for each month
        """
        this_month = datetime.now().replace(day=1)
        prev_val = response.css(".EventNextPrev a::attr(href)").extract_first()
        # Parse the __EVENTARGUMENT value from the JS string
        arg_str = re.search(r"(?<=')V\d+", prev_val).group()
        arg_num = int(arg_str[1:])

        for month_diff in range(-2, 4):
            month = this_month + relativedelta(months=month_diff)
            diff_days = (month - this_month).days
            payload = {
                "ScriptManager": "dnn$ctr426$Events_UP|dnn$ctr426$Events$EventMonth$EventCalendar",
                "__EVENTTARGET": "dnn$ctr426$Events$EventMonth$EventCalendar",
                "__EVENTARGUMENT": "V{}".format(arg_num + diff_days),
                "__VIEWSTATE": response.css("#__VIEWSTATE::attr(value)").extract_first(),
                "__VIEWSTATEGENERATOR":
                    response.css("#__VIEWSTATEGENERATOR::attr(value)").extract_first(),
                "__EVENTVALIDATION":
                    response.css("#__EVENTVALIDATION::attr(value)").extract_first(),
                "dnn$ctr426$Events$EventMonth$SelectCategory$ddlCategories": "All",
            }
            yield FormRequest(
                response.urljoin("/Community-Action/Calendar"),
                formdata=payload,
                callback=self._parse_calendar_response,
                dont_filter=True,
            )

    def _parse_calendar_response(self, response):
        for link in response.css(".EventDay a"):
            link_text = " ".join(link.css("*::text").extract())
            if "Board" in link_text:
                yield response.follow(
                    link.attrib["href"],
                    callback=self._parse_detail,
                    dont_filter=True,
                )

    def _parse_detail(self, response):
        board_start, board_end = self._parse_start_end(response)
        board_title = self._parse_title(response)
        if not board_start:
            return
        location = self._parse_location(response)
        meeting_items = ([(board_title, board_start, board_end)] +
                         self._parse_committees(response, board_start))

        for title, start, end in meeting_items:
            classification = self._parse_classification(title)
            meeting = Meeting(
                title=title,
                description="",
                classification=classification,
                start=start,
                end=end,
                all_day=False,
                time_notes="",
                location=location,
                links=self._parse_links(classification, start),
                source=response.url,
            )

            meeting["status"] = self._get_status(meeting)
            meeting["id"] = self._get_id(meeting)

            yield meeting

    def _parse_title(self, response):
        """Parse or generate meeting title."""
        title_str = response.css(".SubHead .Head::text").extract_first().strip()
        return re.sub(r"(Committees|&|Meeting)", "", title_str).strip()

    def _parse_classification(self, title):
        if "Board" in title:
            return BOARD
        return COMMITTEE

    def _parse_start_end(self, response):
        """Parse start, end datetimes as naive datetime objects."""
        dt_strs = []
        for detail_str in response.css(".DetailContentRight *::text").extract():
            dt_match = re.search(
                r"[A-Z][a-z]{2,8} \d{1,2}, \d{4} \d{1,2}:\d{2} [APM]{2}", detail_str
            )
            if dt_match:
                dt_strs.append(dt_match.group())
        if len(dt_strs) == 0:
            return None, None
        start = datetime.strptime(dt_strs[0].lower(), "%B %d, %Y %I:%M %p")
        end = None
        if len(dt_strs) > 1:
            end = datetime.strptime(dt_strs[1].lower(), "%B %d, %Y %I:%M %p")
        return start, end

    def _parse_committees(self, response, start):
        """Parse title, start, end tuples of committee meetings (if available)"""
        committees = []
        for line in response.css(".DetailContentRight div.Normal > p::text").extract():
            line_str = re.sub(r"\s+", " ", line.strip())
            meeting_match = re.search(r"^[A-Z][A-Za-z:&\d\- ]+ [apm\.]{2,4}$", line_str)
            if not meeting_match:
                continue
            title_str, time_str = line_str.split(":", 1)
            if "Board" in title_str:
                continue
            title = re.sub(r"(\s+|Meeting)", " ", title_str).strip()
            dur_str, apm_str = time_str.strip().split(" ", 1)
            apm_str = apm_str.replace(".", "")
            time_strs = dur_str.split("-")
            start = datetime.combine(start.date(), self._parse_time_str(time_strs[0] + apm_str))
            end = None
            if len(time_strs) > 1:
                end = datetime.combine(start.date(), self._parse_time_str(time_strs[1] + apm_str))
            committees.append((title, start, end))
        return committees

    def _parse_time_str(self, time_str):
        time_fmt = "%I:%M%p"
        if ":" not in time_str:
            time_fmt = "%I%p"
        return datetime.strptime(time_str, time_fmt).time()

    def _parse_location(self, response):
        """Parse or generate location."""
        loc_str = ""
        for detail_el in response.css(".DetailContentLeft"):
            detail_str = " ".join(detail_el.css("*::text").extract())
            if "Location" not in detail_str:
                continue
            loc_str = " ".join(
                detail_el.xpath("./following-sibling::div[1]").css("*::text").extract()
            ).strip()
        if not loc_str or "Children Services" in loc_str:
            return self.location
        return {
            "name": "",
            "address": loc_str,
        }

    def _parse_links(self, classification, start):
        """Parse or generate links."""
        if classification == BOARD:
            return self.link_date_map[start.strftime("%B %Y")]
        return []
