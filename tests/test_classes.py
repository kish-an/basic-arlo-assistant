import pytest

from baa.classes import ButterAttendee, ArloRegistration, AttendanceStatus


@pytest.fixture
def meeting_attendees():
    return [
        ButterAttendee(
            name="Ada Lovelace", email="ada@example.com", session_duration=105.24
        ),
        ButterAttendee(
            name="Mary Shelley", email="mry@example.com", session_duration=120.0
        ),
    ]


def test_arlo_reg_butter_attendee_equality(meeting_attendees):
    arlo_reg1 = ArloRegistration(
        name="Ada Lo", email="ada@example.com", reg_href="href"
    )
    arlo_reg2 = ArloRegistration(
        name="Mary Shelley", email="mary@example.com", reg_href="href2"
    )
    assert arlo_reg1 in meeting_attendees
    assert arlo_reg2 in meeting_attendees


def test_attendance_status_enum():
    assert AttendanceStatus.ATTENDED.value == "Attended"
    assert AttendanceStatus.DID_NOT_ATTEND.value == "DidNotAttend"
    assert AttendanceStatus.UNKNOWN.value == "Unknown"
