import csv
from pathlib import Path
from datetime import datetime
from itertools import islice
from typing import Any

from baa.exceptions import EventNotFound, AttendeeFileProcessingError
from baa.classes import ButterAttendee, Meeting


def extract_metadata(rows: list[str], event_code: str | None) -> tuple[str, datetime]:
    """Get meeting details from metadata"""
    for i, row in enumerate(rows):
        row = row.strip().replace(",", "")
        # 1st row is the room name, which should contain the event code at the end. This will identify the Arlo Event
        if i == 0 and event_code is None:
            if row.find("CK") == -1:
                raise EventNotFound(
                    "🚨 The event code could not be found from the Butter room name. Use the --event-code option instead"
                )
            event_code = row[row.find("CK") :]

        # 3rd/4th rows contains start/end dates which will identify the Arlo EventSession. We only need the DD/MM/YYYY
        elif i == 2:
            # Expected date format: Sep 08 2024 - 06:30 PM
            date_str = row.replace('"', "").replace("Started at: ", "")
            meeting_start = datetime.strptime(date_str, "%b %d %Y - %H:%M %p")
            continue

    return (event_code, meeting_start)


def get_attendees(attendee_file: Path, event_code: str | None) -> Meeting:
    """Get list of attendees from Butter attendance report csv"""
    # Key = Email, Value = Row of attendee from csv.DictReader
    unique_attendees: dict[str, dict[str, Any]] = dict()

    try:
        with open(attendee_file) as attendee_list:
            event_code, meeting_start = extract_metadata(
                list(islice(attendee_list, 6)), event_code
            )

            for attendee in csv.DictReader(attendee_list):
                duration = float(attendee["Duration in session (minutes)"])
                attendee["Duration in session (minutes)"] = duration

                if attendee["Type"] == "temp-host" or duration == 0:
                    continue

                # If this is a duplicate entry, add session duration to existing entry
                email = attendee["Email"]
                if email in unique_attendees:
                    unique_attendees[email]["Duration in session (minutes)"] += duration
                else:
                    unique_attendees[email] = attendee
    except Exception as e:
        raise AttendeeFileProcessingError(
            f"🚨 An error occured while processing ATTENDEE_FILE: {e}"
        )

    attendees: list[ButterAttendee] = []
    for attendee in unique_attendees.values():
        attendees.append(
            ButterAttendee(
                name=attendee["Name"],
                email=attendee["Email"],
                session_duration=attendee["Duration in session (minutes)"],
            )
        )

    return Meeting(event_code, meeting_start, attendees)
