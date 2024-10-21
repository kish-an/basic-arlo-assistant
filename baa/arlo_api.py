import requests
from requests.auth import HTTPBasicAuth
from lxml import etree
from datetime import datetime

from baa.helpers import get_keyring_credentials, remove_keyring_credentials
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
        self.missing_students = []

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

    def _get_event_id(self, event_code: str) -> str:
        res = self._get_response(f"{self.base_url}/events", params={"expand": "Event"})

        event_tree = self._append_paginated(root=etree.fromstring(res.content))
        event_id = event_tree.findtext(f".//Code[. ='{event_code}']/../EventID")
        if event_id is None:
            raise CourseCodeNotFound(
                f"🚨 Could not find any events corresponding to the event code: {event_code}"
            )

        return event_id

    def _get_session_id(self, event_id: str, start_date: datetime) -> str:
        res = self._get_response(
            f"{self.base_url}/events/{event_id}/sessions",
            params={"expand": "EventSession"},
        )

        date = start_date.strftime("%Y-%m-%d")
        session_tree = self._append_paginated(root=etree.fromstring(res.content))

        session_ids = session_tree.xpath(
            f".//StartDateTime[contains(text(),'{date}')]/preceding-sibling::SessionID/text()"
        )
        if len(session_ids) == 0:
            raise SessionNotFound(f"🚨 No session found on: {date}")

        return session_ids[0]

    def _get_session_registrations(self, session_id: str) -> etree._Element:
        res = self._get_response(
            f"{self.base_url}/eventsessions/{session_id}/registrations",
            params={
                "expand": "EventSessionRegistration,EventSessionRegistration/ParentRegistration,EventSessionRegistration/ParentRegistration/Contact"
            },
        )

        reg_tree = self._append_paginated(root=etree.fromstring(res.content))

        return reg_tree

    def get_registrations(
        self, event_code: str, session_date: datetime
    ) -> etree._Element:
        event_id = self._get_event_id(event_code)
        session_id = self._get_session_id(event_id, session_date)
        return self._get_session_registrations(session_id)

    def update_attendance(session_reg_href: str) -> bool:
        pass
