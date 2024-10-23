from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List
from datetime import datetime


@dataclass(order=True)
class Attendee:
    """Individual attendee details"""

    email: str
    name: str
    session_duration: Optional[float] = field(default=None, compare=False)
    reg_href: Optional[str] = field(default=None, compare=False)
    attendance_registered: Optional[bool] = field(default=False, compare=False)


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
