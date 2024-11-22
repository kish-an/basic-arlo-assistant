import logging
import httpx
from lxml import etree
from copy import deepcopy
from datetime import datetime
from typing import Iterator

from baa.helpers import (
    get_keyring_credentials,
    remove_keyring_credentials,
)
from baa.classes import AttendanceStatus, ArloRegistration
from baa.exceptions import (
    AuthenticationFailed,
    ApiCommunicationFailure,
    EventNotFound,
    SessionNotFound,
)

logger = logging.getLogger(__name__)


class ArloClient:
    """
    A client for interacting with the Arlo API.

    This client handles authentication, API requests, and response processing
    to manage Events, EventSessions, and EventSessionRegistrations within the Arlo training managament platform.
    """

    def __init__(self, platform: str):
        """
        Initialize the ArloClient.

        Args:
            platform (str): The platform subdomain (e.g., "myarlo") for API requests.
        """
        self.base_url = f"https://{platform}.arlo.co/api/2012-02-01/auth/resources"
        auth = httpx.BasicAuth(*get_keyring_credentials())
        self.client = httpx.Client(auth=auth)
        self.async_client = httpx.AsyncClient(auth=auth, http2=True)
        self.event_cache: dict[str, etree._Element] = {}
        self.session_cache: dict[str, etree._Element] = {}
        logger.debug(f"Initialising ArloClient for {self.base_url}")

    def _get_response(self, url: str, params: dict = None) -> httpx.Response:
        """
        Sends a GET request to the specified URL and handles authentication errors.

        Args:
            url (str): The URL to send the request to.
            params (dict, optional): Query parameters for the request.

        Raises:
            AuthenticationFailed: If authentication fails.
            ApiCommunicationFailure: If the API response is not 200 OK.

        Returns:
            requests.Response: The response from the API.
        """
        res = self.client.get(url, params=params)
        if res.status_code == 401:
            remove_keyring_credentials()
            raise AuthenticationFailed(
                "🚨 Authentication to the Arlo API failed. Ensure you have provided the correct credentials"
            )
        elif not res.is_success:
            raise ApiCommunicationFailure("🚨 Unable to communicate with the Arlo API")

        return res

    def _append_paginated(self, root: etree._Element) -> etree._Element:
        """
        Fetches additional pages of results and appends to the root element if the API indicates more pages are available (Link element with rel atrribute set to next)

        Args:
            root (etree._Element): The root element to append results to.

        Returns:
            etree._Element: The updated root element with appended paginated results.
        """
        next_link = root.find("./Link[@rel='next']")

        while next_link is not None:
            res = self._get_response(next_link.get("href"))

            next_page = etree.fromstring(res.content)
            for elem in next_page:
                # Copy element as appending will reparent the node
                root.append(deepcopy(elem))

            next_link = next_page.find("./Link[@rel='next']")

        return root

    def _get_event_tree(self, event_code: str) -> etree._Element:
        """
        Retrieves the Events XML tree for a specific event code.

        Args:
            event_code (str): The event code to retrieve.

        Raises:
            EventNotFound: If the event cannot be found.

        Returns:
            etree._Element: The event tree.
        """
        if event_code in self.event_cache:
            return self.event_cache[event_code]

        res = self._get_response(f"{self.base_url}/events", params={"expand": "Event"})
        event_tree = self._append_paginated(root=etree.fromstring(res.content))
        self.event_cache[event_code] = event_tree
        return event_tree

    def _get_session_tree(self, event_id: str) -> etree._Element:
        """
        Retrieves the EventSessions XML tree for a specific Event.

        Args:
            event_id (str): The event ID to retrieve sessions for.

        Returns:
            etree._Element: The session tree.
        """
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
        """
        Retrieves the EventID for a given event Code.

        Args:
            event_code (str): The event code to look up.

        Raises:
            EventNotFound: If no event is found for the given code.

        Returns:
            str: The event ID.
        """
        event_tree = self._get_event_tree(event_code)
        event_id = event_tree.findtext(f".//Code[. ='{event_code}']/../EventID")
        if event_id is None:
            raise EventNotFound(
                f"🚨 Could not find any events corresponding to the event code: {event_code}"
            )

        return event_id

    def _get_session_id(self, event_id: str, start_date: datetime) -> str:
        """
        Retrieves the SessionID corresponding to a StartDate for a given EventID.

        Args:
            event_id (str): The event ID to look up.
            start_date (datetime): The start date to match.

        Raises:
            SessionNotFound: If no session is found on the specified date.

        Returns:
            str: The session ID.
        """
        session_tree = self._get_session_tree(event_id)
        date = start_date.strftime("%Y-%m-%d")

        session_ids = session_tree.xpath(
            f".//StartDateTime[contains(text(),'{date}')]/preceding-sibling::SessionID/text()"
        )
        if len(session_ids) == 0:
            raise SessionNotFound(f"🚨 No session found on: {date}")

        return session_ids[0]

    def _get_registrations_tree(self, session_id: str) -> etree._Element:
        """
        Retrieves the EventSessionRegistrations tree for a specific EventSession ID.

        Args:
            session_id (str): The session ID to look up.

        Returns:
            etree._Element: The registrations tree.
        """
        res = self._get_response(
            f"{self.base_url}/eventsessions/{session_id}/registrations",
            params={
                "expand": "EventSessionRegistration,EventSessionRegistration/ParentRegistration,EventSessionRegistration/ParentRegistration/Contact"
            },
        )
        reg_tree = self._append_paginated(root=etree.fromstring(res.content))

        return reg_tree

    def get_event_name(self, event_code: str) -> str:
        """
        Retrieves the name of an Event given its code.

        Args:
            event_code (str): The event code to look up.

        Returns:
            str: The name of the event, or "Not found" if it does not exist.
        """
        event_tree = self._get_event_tree(event_code)

        return event_tree.findtext(f".//Code[. ='{event_code}']/../Name") or "Not found"

    def get_session_name(self, event_code: str, start_date: datetime) -> str:
        """
        Retrieves the name of an EventSession for a given event code and start date.

        Args:
            event_code (str): The event code to look up.
            start_date (datetime): The start date to match.

        Returns:
            str: The name of the session, or "Not found" if it does not exist.
        """
        event_id = self._get_event_id(event_code)
        session_tree = self._get_session_tree(event_id)

        date = start_date.strftime("%Y-%m-%d")
        session_names = session_tree.xpath(
            f".//StartDateTime[contains(text(),'{date}')]/preceding-sibling::Name/text()"
        )
        return "Not found" if len(session_names) == 0 else session_names[0]

    def get_registrations(
        self, event_code: str, session_date: datetime
    ) -> Iterator[ArloRegistration]:
        """
        Retrieves registrations for a specific event code and session date.

        Args:
            event_code (str): The event code to look up.
            session_date (datetime): The date of the session.

        Yields:
            ArloRegistration: The registration information for each contact.
        """
        logger.debug(
            f"Retrieving registrations for event {event_code}, from {session_date}"
        )
        event_id = self._get_event_id(event_code)
        session_id = self._get_session_id(event_id, session_date)
        registrations = self._get_registrations_tree(session_id)

        for reg in registrations.findall(".//Contact"):
            status = reg.getparent().getparent().find("./Status").text
            if status == "Cancelled":
                continue

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

            yield ArloRegistration(
                name=f"{first_name} {last_name}",
                email=email,
                reg_href=reg_href,
            )

    async def update_attendance(
        self, session_reg_href: str, attendance: AttendanceStatus
    ) -> bool:
        """
        Updates the attendance status for a specific EventSessionRegistration.

        Args:
            session_reg_href (str): The href link to the EventSessionRegistration. In the format: https://{base_url}/registrations/{parent_registration_id}/sessionregistrations/{session_registration_id}
            attendance (AttendanceStatus): The attendance status to update.

        Returns:
            bool: True if the update was successful, otherwise False.
        """
        headers = {"Content-Type": "application/xml"}
        payload = f"""<?xml version="1.0" encoding="utf-8"?>
        <diff>
            <replace sel="EventSessionRegistration/Attendance/text()[1]">{attendance.value}</replace>
        </diff>
        """
        res = await self.async_client.patch(
            session_reg_href, content=payload, headers=headers
        )
        if not res.is_success:
            logger.error(
                f"Unable to update attendance: {res.status_code} {res.content}"
            )
        return res.is_success

    async def close(self) -> None:
        """Close the sync and async httpx clients"""
        self.client.close()
        await self.async_client.aclose()
