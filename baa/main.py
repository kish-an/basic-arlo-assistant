from pathlib import Path
from typing import Optional

from baa.attendee_parser import butter
from baa.arlo_api import get_event


def baa(
    attendee_file: Path,
    format: str,
    platform: str,
    course_code: Optional[str],
) -> None:
    meeting = butter.get_attendees(attendee_file, course_code)
    meeting.attendees.sort()

    get_event(platform, meeting.course_code)
