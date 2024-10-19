import csv
from pathlib import Path
from datetime import datetime
from itertools import islice
from typing import Optional, List, Tuple, Any

from baa.exceptions import CourseCodeNotFound
from baa.attendee_parser.attendee import Attendee, Meeting


def extract_metadata(
    rows: List[str], course_code: Optional[str]
) -> Tuple[str, datetime]:
    """Get meeting details from metadata"""
    for i, row in enumerate(rows):
        row = row.strip().replace(",", "")
        # 1st row is the room name, which should contain the course code at the end. This will identify the Arlo Event
        if i == 0 and course_code is None:
            if row.find("CK") == -1:
                raise CourseCodeNotFound(
                    "The course code could not be found from the Butter room name. Use the --course-code option instead."
                )
            course_code = row[row.find("CK") :]

        # 3rd/4th rows contains start/end dates which will identify the Arlo EventSession. We only need the DD/MM/YYYY
        elif i == 2:
            # Expected date format example: Sep 08 2024 - 06:30 PM
            date_str = row.replace('"', "").replace("Started at: ", "")
            meeting_start = datetime.strptime(date_str, "%b %d %Y - %H:%M %p")
            continue

    return (course_code, meeting_start)


def get_attendees(attendee_file: Path, course_code: Optional[str]) -> Meeting:
    """Get list of attendees from Butter attendance report csv"""
    # Key = Email, Value = Row of attendee from csv.DictReader
    unique_attendees: dict[str, dict[str, Any]] = dict()

    with open(attendee_file) as attendee_list:
        course_code, meeting_start = extract_metadata(
            list(islice(attendee_list, 6)), course_code
        )

        for attendee in csv.DictReader(attendee_list):
            if attendee["Type"] == "temp-host":
                continue

            duration = float(attendee["Duration in session (minutes)"])
            attendee["Duration in session (minutes)"] = duration

            # If this is a duplicate entry, add session duration to existing entry
            email = attendee["Email"]
            if email in unique_attendees:
                unique_attendees[email]["Duration in session (minutes)"] += duration
            else:
                unique_attendees[email] = attendee

    meeting = Meeting(
        course_code=course_code, start_date=meeting_start, attendees=list()
    )
    for attendee in unique_attendees.values():
        meeting.attendees.append(
            Attendee(
                name=attendee["Name"],
                email=attendee["Email"],
                session_duration=attendee["Duration in session (minutes)"],
            )
        )

    return meeting
