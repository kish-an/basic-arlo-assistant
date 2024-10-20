import requests
from requests.auth import HTTPBasicAuth
from xml.etree import ElementTree

from baa.helpers import get_keyring_credentials, remove_keyring_credentials
from baa.exceptions import (
    AuthenticationFailed,
    ApiCommunicationFailure,
    CourseCodeNotFound,
)


def append_paginated(
    root: ElementTree.Element, session: requests.Session
) -> ElementTree.Element:
    next = root.find("./Link[@rel='next']")

    while next is not None:
        res = session.get(next.get("href"))

        next_page = ElementTree.fromstring(res.content)
        # Append all children elements to root tree
        for elem in next_page.findall("*"):
            root.append(elem)

        next = next_page.find("./Link[@rel='next']")

    return root


def get_event(platform: str, event_code: str) -> str:
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

    event_tree = append_paginated(
        root=ElementTree.fromstring(res.content), session=session
    )
    event_id = getattr(
        event_tree.find(f".//Code[. = '{event_code}']/../EventID"), "text", None
    )
    if event_id is None:
        raise CourseCodeNotFound(
            f"🚨 Could not find any events corresponding to the event code: {event_code}"
        )

    return event_id


def get_session():
    pass
