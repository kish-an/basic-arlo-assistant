import requests
from requests.auth import HTTPBasicAuth
from xml.etree import ElementTree

from baa.helpers import get_keyring_credentials, remove_keyring_credentials
from baa.exceptions import AuthenticationFailed, ApiCommunicationFailure


def get_event(platform: str, course_code: str):
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

    print(res.content)
    events_tree = ElementTree.fromstring(res.content)
