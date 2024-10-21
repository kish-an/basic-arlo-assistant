from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List
from datetime import datetime


@dataclass(order=True)
class Attendee:
    """Individual attendee details"""

    name: str
    email: str
    session_duration: Optional[float] = field(default=None, compare=False)


@dataclass
class Meeting:
    """Meeting details"""

    event_code: str
    start_date: datetime
    attendees: List[Attendee]


class Attendance(Enum):
    ATTENDED = "Attended"
    DID_NOT_ATTEND = "DidNotAttend"
    UNKNOWN = "Unknown"
