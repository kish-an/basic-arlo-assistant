import requests
from requests.auth import HTTPBasicAuth
from lxml import etree
from datetime import datetime
from typing import Generator, Dict

from baa.helpers import (
    get_keyring_credentials,
    remove_keyring_credentials,
    LoadingSpinner,
)
from baa.classes import AttendanceStatus, Attendee
from baa.exceptions import (
    AuthenticationFailed,
    ApiCommunicationFailure,
    CourseCodeNotFound,
    SessionNotFound,
)


class ArloClient:
    def __init__(self, platform: str):
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(*get_keyring_credentials())
        self.base_url = f"https://{platform}.arlo.co/api/2012-02-01/auth/resources"
        self.event_cache: Dict[str, etree._Element] = {}
        self.session_cache: Dict[str, etree._Element] = {}

    def _get_response(self, url: str, params: dict = None) -> requests.Response:
        res = self.session.get(url, params=params)
        if res.status_code == 401:
            remove_keyring_credentials()
            raise AuthenticationFailed(
                "🚨 Authentication to the Arlo API failed. Ensure you have provided the correct credentials"
            )
        elif res.status_code != 200:
            raise ApiCommunicationFailure("🚨 Unable to communicate with the Arlo API")

        return res

    def _append_paginated(self, root: etree._Element) -> etree._Element:
        next_link = root.find("./Link[@rel='next']")

        while next_link is not None:
            res = self._get_response(next_link.get("href"))

            next_page = etree.fromstring(res.content)
            for elem in next_page:
                root.append(elem)

            next_link = next_page.find("./Link[@rel='next']")

        return root

    def _get_event_tree(self, event_code: str) -> etree._Element:
        if event_code in self.event_cache:
            return self.event_cache[event_code]

        res = self._get_response(f"{self.base_url}/events", params={"expand": "Event"})
        event_tree = self._append_paginated(root=etree.fromstring(res.content))
        self.event_cache[event_code] = event_tree
        return event_tree

    def _get_session_tree(self, event_id: str) -> etree._Element:
        if event_id in self.session_cache:
            return self.session_cache[event_id]

        res = self._get_response(
            f"{self.base_url}/events/{event_id}/sessions",
            params={"expand": "EventSession"},
        )
        session_tree = self._append_paginated(root=etree.fromstring(res.content))
        self.session_cache[event_id] = session_tree
        return session_tree

    def _get_event_id(self, event_code: str) -> str:
        event_tree = self._get_event_tree(event_code)
        event_id = event_tree.findtext(f".//Code[. ='{event_code}']/../EventID")
        if event_id is None:
            raise CourseCodeNotFound(
                f"🚨 Could not find any events corresponding to the event code: {event_code}"
            )

        return event_id

    def _get_session_id(self, event_id: str, start_date: datetime) -> str:
        session_tree = self._get_session_tree(event_id)
        date = start_date.strftime("%Y-%m-%d")

        session_ids = session_tree.xpath(
            f".//StartDateTime[contains(text(),'{date}')]/preceding-sibling::SessionID/text()"
        )
        if len(session_ids) == 0:
            raise SessionNotFound(f"🚨 No session found on: {date}")

        return session_ids[0]

    def _get_registrations_tree(self, session_id: str) -> etree._Element:
        with LoadingSpinner("Loading registrations from Arlo..."):
            res = self._get_response(
                f"{self.base_url}/eventsessions/{session_id}/registrations",
                params={
                    "expand": "EventSessionRegistration,EventSessionRegistration/ParentRegistration,EventSessionRegistration/ParentRegistration/Contact"
                },
            )
            reg_tree = self._append_paginated(root=etree.fromstring(res.content))

        return reg_tree

    def get_event_name(self, event_code: str) -> str:
        event_tree = self._get_event_tree(event_code)

        return event_tree.findtext(f".//Code[. ='{event_code}']/../Name")

    def get_session_name(self, event_code: str, start_date: datetime) -> str:
        event_id = self._get_event_id(event_code)
        session_tree = self._get_session_tree(event_id)

        date = start_date.strftime("%Y-%m-%d")
        session_names = session_tree.xpath(
            f".//StartDateTime[contains(text(),'{date}')]/preceding-sibling::Name/text()"
        )
        return None if len(session_names) == 0 else session_names[0]

    def get_registrations(
        self, event_code: str, session_date: datetime
    ) -> Generator[Attendee, None, None]:
        event_id = self._get_event_id(event_code)
        session_id = self._get_session_id(event_id, session_date)
        registrations = self._get_registrations_tree(session_id)

        for reg in registrations.findall(".//Contact"):
            first_name = reg.find("./FirstName").text
            last_name = reg.find("./LastName").text
            email = reg.find("./Email").text
            # Traverse back up to Link with event session registration href
            reg_href = (
                reg.getparent()
                .getparent()
                .getparent()
                .getparent()
                .getparent()
                .get("href")
            )

            yield Attendee(
                name=f"{first_name} {last_name}", email=email, reg_href=reg_href
            )

    def update_attendance(
        self, session_reg_href: str, attendance: AttendanceStatus
    ) -> bool:
        headers = {"Content-Type": "application/xml"}
        payload = f"""<?xml version="1.0" encoding="utf-8"?>
        <diff>
            <replace sel="EventSessionRegistration/Attendance/text()[1]">{attendance.value}</replace>
        </diff>
        """

        res = self.session.patch(session_reg_href, data=payload, headers=headers)
        return res.status_code == 200
