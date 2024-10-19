from pathlib import Path
from typing import Optional
from baa.attendee_parser import butter


def baa(
    attendee_file: Path,
    format: str,
    platform: str,
    course_code: Optional[str],
    username: str,
    password: str,
) -> None:
    meeting = butter.get_attendees(attendee_file, course_code)
