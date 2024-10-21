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


def append_paginated(root: etree._Element, session: requests.Session) -> etree._Element:
    next_link = root.find("./Link[@rel='next']")

    while next_link is not None:
        res = session.get(next_link.get("href"))

        next_page = etree.fromstring(res.content)
        for elem in next_page:
            root.append(elem)

        next_link = next_page.find("./Link[@rel='next']")

    return root


def get_event_id(platform: str, event_code: str) -> str:
    session = requests.Session()
    session.auth = HTTPBasicAuth(*get_keyring_credentials())

    base_url = f"https://{platform}.arlo.co/api/2012-02-01/auth/resources"

    res = session.get(f"{base_url}/events", params={"expand": "Event"})
    if res.status_code == 401:
        remove_keyring_credentials()
        raise AuthenticationFailed(
            "🚨 Authentication to the Arlo API failed. Ensure you have provided the correct credentials"
        )
    elif res.status_code != 200:
        raise ApiCommunicationFailure("🚨 Unable to communicate with the Arlo API")

    event_tree = append_paginated(root=etree.fromstring(res.content), session=session)
    event_id = event_tree.findtext(f".//Code[. ='{event_code}']/../EventID")
    if event_id is None:
        raise CourseCodeNotFound(
            f"🚨 Could not find any events corresponding to the event code: {event_code}"
        )

    return event_id


def get_session():
    pass
