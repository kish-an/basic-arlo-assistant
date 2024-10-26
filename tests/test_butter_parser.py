import pytest
import csv
from datetime import datetime
from baa.attendee_parser.butter import get_attendees, extract_metadata
from baa.exceptions import EventNotFound, AttendeeFileProcessingError


def test_extract_metadata_valid():
    rows = [
        "Room name: Title CK24ABC,,,,,",
        "Room ID: ABCXYZ,,,,,",
        '"Started at: Jan 01 2024 - 06:30 PM",,,,,',
        '"Ended at: Jan 01 2024 - 08:30 PM",,,,,',
        ",,,,,",
        ",,,,,",
    ]
    event_code, meeting_start = extract_metadata(rows, None)
    assert event_code == "CK24ABC"
    assert meeting_start == datetime(2024, 1, 1, 6, 30)


def test_extract_metadata_missing_event_code():
    rows = [
        "Room name: Title,,,,,",
        "Room ID: ABCXYZ,,,,,",
        '"Started at: Jan 01 2024 - 06:30 PM",,,,,',
        '"Ended at: Jan 01 2024 - 08:30 PM",,,,,',
        ",,,,,",
        ",,,,,",
    ]
    with pytest.raises(EventNotFound):
        extract_metadata(rows, None)


def test_get_attendees_valid(tmp_path):
    attendee_file = tmp_path / "temp_participant_list.csv"
    with attendee_file.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Room name: Title CK24ABC", "", "", "", "", ""])
        writer.writerow(["Room ID: ABCXYZ", "", "", "", "", ""])
        writer.writerow(["Started at: Jan 01 2024 - 06:30 PM", "", "", "", "", ""])
        writer.writerow(["Ended at: Jan 01 2024 - 08:30 PM", "", "", "", "", ""])
        writer.writerow(["", "", "", "", "", ""])
        writer.writerow(["", "", "", "", "", ""])
        writer.writerow(
            [
                "Name",
                "Email",
                "Type",
                "Channel id",
                "First join at",
                "Duration in session (minutes)",
            ]
        )
        writer.writerow(
            [
                "Rosalind Franklin",
                "rosalind@example.com",
                "temp-host",
                "main",
                "18:25:30",
                "143.36",
            ]
        )
        writer.writerow(
            [
                "Grace Hopper",
                "grace@example.com",
                "participant",
                "main",
                "18:31:46",
                "123.52",
            ]
        )
        writer.writerow(
            [
                "Katherine Johnson",
                "katherine@example.com",
                "participant",
                "main",
                "18:35:29",
                "118.73",
            ]
        )

    meeting = get_attendees(attendee_file, event_code=None)
    assert meeting.event_code == "CK24ABC"
    assert len(meeting.attendees) == 2
    assert (
        meeting.attendees[0].name == "Grace Hopper"
        and meeting.attendees[0].email == "grace@example.com"
        and meeting.attendees[0].session_duration == 123.52
    )
    assert (
        meeting.attendees[1].name == "Katherine Johnson"
        and meeting.attendees[1].email == "katherine@example.com"
        and meeting.attendees[1].session_duration == 118.73
    )


def test_get_attendees_invalid(tmp_path):
    attendee_file = tmp_path / "temp_attendee_file.csv"
    attendee_file.write_text("temp", encoding="utf-8")
    attendee_file.chmod(0)
    with pytest.raises(AttendeeFileProcessingError):
        get_attendees(attendee_file, event_code=None)
