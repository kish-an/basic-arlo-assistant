from dataclasses import dataclass
from enum import Enum
from typing import Optional, List
from datetime import datetime


@dataclass(order=True)
class Attendee:
    """Individual attendee details"""

    name: str
    email: Optional[str] = None
    session_duration: Optional[float] = None
    reg_id: Optional[str] = None


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
