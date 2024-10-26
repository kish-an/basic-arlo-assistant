import pytest

from baa.main import baa
from baa.classes import ButterAttendee, ArloRegistration, AttendanceStatus


@pytest.fixture
def mock_arlo_client(mocker):
    return mocker.patch("baa.main.ArloClient")


@pytest.fixture(autouse=True)
def mock_meeting(mocker):
    mock_meeting = mocker.MagicMock()
    mock_meeting.attendees = [
        ButterAttendee(
            session_duration=60,
            attendance_registered=False,
            name="Maya Angelou",
            email="maya@example.com",
        ),
        ButterAttendee(
            session_duration=110,
            attendance_registered=False,
            name="Amelia Earhart",
            email="amela@example.com",
        ),
    ]
    mocker.patch("baa.attendee_parser.butter.get_attendees", return_value=mock_meeting)
    return mock_meeting


def setup_registration(mocker, mock_arlo_client, name):
    reg = ArloRegistration(
        name=name, email=name.split(" ")[0].lower() + "@example.com", reg_href="href"
    )

    mock_update_attnd = mocker.MagicMock(return_value=True)
    mock_arlo_client.return_value.update_attendance = mock_update_attnd
    mock_arlo_client.return_value.get_registrations.return_value = [reg]

    return reg, mock_update_attnd


def run_baa(tmp_path, min_duration=0, skip_absent=False, dry_run=False):
    baa(
        attendee_file=tmp_path / "test.csv",
        format="dummy_format",
        platform="dummy_platform",
        event_code=None,
        date=None,
        min_duration=min_duration,
        skip_absent=skip_absent,
        dry_run=dry_run,
    )


def test_baa_updates_attendance(mocker, mock_arlo_client, tmp_path):
    reg, mock_update_attnd = setup_registration(
        mocker, mock_arlo_client, "Maya Angelou"
    )
    run_baa(tmp_path)

    assert reg.attendance_registered
    mock_update_attnd.assert_called_with(reg.reg_href, AttendanceStatus.ATTENDED)


def test_baa_registration_absent(mocker, mock_arlo_client, tmp_path):
    reg, mock_update_attnd = setup_registration(
        mocker, mock_arlo_client, "Edith Clarke"
    )
    run_baa(tmp_path)

    assert not reg.attendance_registered
    mock_update_attnd.assert_called_with(reg.reg_href, AttendanceStatus.DID_NOT_ATTEND)


def test_baa_min_duration(mocker, mock_arlo_client, tmp_path):
    reg, mock_update_attnd = setup_registration(
        mocker, mock_arlo_client, "Maya Angelou"
    )
    run_baa(tmp_path, min_duration=90)

    assert not reg.attendance_registered
    mock_update_attnd.assert_called_once_with(
        reg.reg_href, AttendanceStatus.DID_NOT_ATTEND
    )


def test_baa_skip_absent(mocker, mock_arlo_client, tmp_path):
    reg, mock_update_attnd = setup_registration(
        mocker, mock_arlo_client, "Joyce Aylard"
    )
    run_baa(tmp_path, skip_absent=True)

    assert not reg.attendance_registered
    mock_update_attnd.assert_not_called()


def test_baa_dry_run(mocker, mock_arlo_client, tmp_path):
    reg, mock_update_attnd = setup_registration(
        mocker, mock_arlo_client, "Amelia Earhart"
    )
    run_baa(tmp_path, dry_run=True)

    assert reg.attendance_registered
    mock_update_attnd.assert_not_called()


def test_baa_attendee_not_found(mocker, mock_arlo_client, mock_meeting, tmp_path):
    setup_registration(mocker, mock_arlo_client, "Maya Angelou")
    run_baa(tmp_path)

    attendee1, attendee2 = mock_meeting.attendees
    assert attendee1.attendance_registered and not attendee2.attendance_registered


def test_baa_update_failed(mocker, mock_arlo_client, tmp_path):
    reg1 = ArloRegistration(
        name="Maya Angelou", email="maya@example.com", reg_href="href1"
    )
    reg2 = ArloRegistration(
        name="Amelia Earhart", email="amelia@example.com", reg_href="href2"
    )
    # Update attendance for first registration but fail on second
    mock_update_attnd = mocker.MagicMock(side_effect=[True, False])
    mock_arlo_client.return_value.update_attendance = mock_update_attnd
    mock_arlo_client.return_value.get_registrations.return_value = [reg1, reg2]

    run_baa(tmp_path)

    mock_update_attnd.assert_has_calls(
        [
            mocker.call(reg1.reg_href, AttendanceStatus.ATTENDED),
            mocker.call(reg2.reg_href, AttendanceStatus.ATTENDED),
        ]
    )
    assert reg1.attendance_registered
    assert reg2.attendance_registered is None
