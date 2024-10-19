from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime


@dataclass
class Attendee:
    """Individual attendee details"""

    name: str
    email: Optional[str] = None
    session_duration: Optional[float] = None
    reg_id: Optional[str] = None


@dataclass
class Meeting:
    """Meeting details"""

    course_code: str
    start_date: datetime
    attendees: List[Attendee]
