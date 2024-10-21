from pathlib import Path
from datetime import datetime
from typing import Optional

from baa.attendee_parser import butter
from baa.arlo_api import ArloClient


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
    registrations = arlo_client.get_registrations(
        event_code or meeting.event_code, date or meeting.start_date
    )
