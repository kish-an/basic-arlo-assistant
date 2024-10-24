from dataclasses import dataclass
from abc import ABC
from enum import Enum
from typing import Optional, List
from datetime import datetime


@dataclass
class Attendee(ABC):
    """Attendee base class. All format specific attendee classes should derive from this"""

    name: str
    email: str
    attendance_registered: Optional[bool]


@dataclass
class ButterAttendee(Attendee):
    session_duration: float


@dataclass
class ArloRegistration(Attendee):
    reg_href: str

    def __eq__(self, other):
        if not isinstance(other, Attendee):
            return NotImplemented

        if isinstance(other, ButterAttendee):
            return self.name == other.name or self.email == other.email
        else:
            return NotImplemented


@dataclass
class Meeting:
    event_code: str
    start_date: datetime
    attendees: List[Attendee]


class AttendanceStatus(Enum):
    ATTENDED = "Attended"
    DID_NOT_ATTEND = "DidNotAttend"
    UNKNOWN = "Unknown"
