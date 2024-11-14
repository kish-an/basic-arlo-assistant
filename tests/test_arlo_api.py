import pytest
from httpx import Response
from lxml import etree
from datetime import datetime
from baa.arlo_api import ArloClient
from baa.exceptions import (
    AuthenticationFailed,
    ApiCommunicationFailure,
    EventNotFound,
    SessionNotFound,
)
from baa.classes import AttendanceStatus


@pytest.fixture
def arlo_client(mocker):
    mocker.patch("baa.arlo_api.get_keyring_credentials", return_value=("user", "pass"))
    return ArloClient("test-platform")


def mock_response(status_code=200, content=""):
    response = Response(status_code=status_code, content=content.encode("utf-8"))
    return response


def api_example_events(event_code="CK24ABC"):
    return f"""
        <Events>
            <Link title="Event">
                <Event>
                    <EventID>1234</EventID>
                    <Code>{event_code}</Code>
                    <Name>Test Event</Name>
                </Event>
            </Link>
        </Events>
    """


def api_example_event_sessions(start_date="2024-01-01"):
    return f"""
        <Sessions>
            <Link title="EventSession">
                <EventSession>
                    <SessionID>5678</SessionID>
                    <Name>Test Session</Name>
                    <StartDateTime>{start_date}T18:30:00.0000000+01:00</StartDateTime>
                </EventSession>
            </Link>
        </Sessions>
    """


def api_example_event_session_registrations(registrations):
    event_session_regs_xml = ""
    for reg in registrations:
        event_session_regs_xml += f"""
        <Link title="EventSessionRegistration" href="reg-href">
            <EventSessionRegistration>
                <Link title="ParentRegistration">
                    <Registration>
                        <Status>{reg[3]}</Status>
                        <Link title="Contact">
                            <Contact>
                                <FirstName>{reg[0]}</FirstName>
                                <LastName>{reg[1]}</LastName>
                                <Email>{reg[2]}</Email>
                            </Contact>
                        </Link>
                    </Registration>
                </Link>
            </EventSessionRegistration>
        </Link>
        """

    return f"""
        <EventSessionRegistrations>
            {event_session_regs_xml}
        </EventSessionRegistrations>
    """


@pytest.mark.parametrize(
    "status_code, exception",
    [
        (401, AuthenticationFailed),
        (500, ApiCommunicationFailure),
    ],
)
def test_api_exceptions(mocker, arlo_client, status_code, exception):
    mock_remove_creds = mocker.patch("baa.arlo_api.remove_keyring_credentials")
    mocker.patch.object(
        arlo_client.client, "get", return_value=mock_response(status_code)
    )

    with pytest.raises(exception):
        arlo_client._get_response("http://test.url")

    if exception is AuthenticationFailed:
        mock_remove_creds.assert_called_once()


def test_get_event_tree(mocker, arlo_client):
    event_code = "CK24ABC"
    mocker.patch.object(
        arlo_client.client,
        "get",
        return_value=mock_response(200, api_example_events()),
    )

    tree = arlo_client._get_event_tree(event_code)
    assert tree is not None
    # Second call should hit the cache
    tree2 = arlo_client._get_event_tree(event_code)
    assert tree2 is tree


def test_get_session_tree(mocker, arlo_client):
    event_id = "1234"
    mocker.patch.object(
        arlo_client.client,
        "get",
        return_value=mock_response(200, api_example_event_sessions()),
    )

    tree = arlo_client._get_session_tree(event_id)
    assert tree is not None
    # Second call should hit the cache
    tree2 = arlo_client._get_session_tree(event_id)
    assert tree2 is tree


def test_get_event_id(mocker, arlo_client):
    event_code = "CK24ABC"
    mocker.patch.object(
        arlo_client,
        "_get_event_tree",
        return_value=etree.fromstring(api_example_events(event_code)),
    )
    event_id = arlo_client._get_event_id(event_code)
    assert event_id == "1234"


def test_no_evevnt_id(mocker, arlo_client):
    event_code = "CK24ABC"

    with pytest.raises(EventNotFound):
        mocker.patch.object(
            arlo_client,
            "_get_event_tree",
            return_value=etree.fromstring(api_example_events("CK00XYZ")),
        )
        arlo_client._get_event_id(event_code)


def test_get_session_id(mocker, arlo_client):
    event_id = "1234"
    start_date = datetime(2024, 1, 1)
    mocker.patch.object(
        arlo_client,
        "_get_session_tree",
        return_value=etree.fromstring(api_example_event_sessions("2024-01-01")),
    )

    session_id = arlo_client._get_session_id(event_id, start_date)
    assert session_id == "5678"


def test_no_session_id(mocker, arlo_client):
    event_id = "1234"
    start_date = datetime(2024, 1, 1)

    with pytest.raises(SessionNotFound):
        mocker.patch.object(
            arlo_client,
            "_get_session_tree",
            return_value=etree.fromstring(api_example_event_sessions("2024-02-02")),
        )
        arlo_client._get_session_id(event_id, start_date)


def test_get_registrations_tree(mocker, arlo_client):
    session_id = "5678"
    mocker.patch.object(
        arlo_client.client,
        "get",
        return_value=mock_response(
            200,
            api_example_event_session_registrations(
                [("Ada", "Lovelace", "ada@example.com", "Approved")]
            ),
        ),
    )

    tree = arlo_client._get_registrations_tree(session_id)
    assert tree is not None


def test_get_registrations(mocker, arlo_client):
    event_code = "CK24ABC"
    session_date = datetime(2024, 1, 1)
    mocker.patch.object(arlo_client, "_get_event_id", return_value="1234")
    mocker.patch.object(arlo_client, "_get_session_id", return_value="4567")
    mocker.patch.object(
        arlo_client,
        "_get_registrations_tree",
        return_value=etree.fromstring(
            api_example_event_session_registrations(
                [
                    ("Ada", "Lovelace", "ada@example.com", "Approved"),
                    ("Dorothy", "Hodgkin", "dorothy@example.com", "Cancelled"),
                ]
            )
        ),
    )

    registrations = list(arlo_client.get_registrations(event_code, session_date))
    # Cancelled registration should not be returned
    assert len(registrations) == 1
    assert registrations[0].name == "Ada Lovelace"
    assert registrations[0].email == "ada@example.com"
    assert registrations[0].reg_href == "reg-href"


def test_update_attendance(mocker, arlo_client):
    session_reg_href = "http://test.url/registration"
    mocker.patch.object(arlo_client.session, "patch", return_value=mock_response(200))
    assert arlo_client.update_attendance(session_reg_href, AttendanceStatus.ATTENDED)

    mocker.patch.object(arlo_client.session, "patch", return_value=mock_response(500))
    assert not arlo_client.update_attendance(
        session_reg_href, AttendanceStatus.ATTENDED
    )


def test_append_paginated(mocker, arlo_client):
    second_page_content = """
        <Root>
            <Item>Second Item</Item>
            <Link rel="next" href="http://test.url/next2"/>
        </Root>
    """
    final_page_content = """
        <Root>
            <Item>Final Item</Item>
        </Root>
    """
    mocker.patch.object(
        arlo_client.client,
        "get",
        side_effect=[
            mock_response(200, second_page_content),
            mock_response(200, final_page_content),
        ],
    )

    result = arlo_client._append_paginated(
        etree.fromstring(
            """
        <Root>
            <Item>First Item</Item>
            <Link rel="next" href="http://test.url/next"/>
        </Root>
    """
        )
    )
    assert len(result.findall(".//Item")) == 3
    assert result.findtext(".//Item[1]") == "First Item"
    assert result.findtext(".//Item[2]") == "Second Item"
    assert result.findtext(".//Item[3]") == "Final Item"


def test_get_event_name(mocker, arlo_client):
    event_code = "CK24ABC"
    mocker.patch.object(
        arlo_client,
        "_get_event_tree",
        return_value=etree.fromstring(api_example_events(event_code)),
    )

    event_name = arlo_client.get_event_name(event_code)
    assert event_name == "Test Event"


def test_get_session_name(arlo_client, mocker):
    event_code = "CK24ABC"
    start_date = datetime(2024, 1, 1)
    mocker.patch.object(arlo_client, "_get_event_id", return_value="1234")
    mocker.patch.object(
        arlo_client,
        "_get_session_tree",
        return_value=etree.fromstring(api_example_event_sessions("2024-01-01")),
    )

    name = arlo_client.get_session_name(event_code, start_date)
    assert name == "Test Session"
