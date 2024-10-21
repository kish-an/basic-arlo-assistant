from pathlib import Path
from datetime import datetime
from typing import Optional

from baa.attendee_parser import butter
from baa.arlo_api import ArloClient
from baa.classes import Attendance


def baa(
    attendee_file: Path,
    format: str,
    platform: str,
    event_code: Optional[str],
    date: Optional[datetime],
    skip_absent: bool,
) -> None:
    meeting = butter.get_attendees(attendee_file, event_code)
    meeting.attendees.sort()

    arlo_client = ArloClient(platform)

    for reg, reg_href in arlo_client.get_registrations(
        event_code=event_code or meeting.event_code,
        session_date=date or meeting.start_date,
    ):
        print(reg, reg_href)
