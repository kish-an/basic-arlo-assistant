from dataclasses import dataclass
from abc import ABC
from enum import Enum
from datetime import datetime


@dataclass(kw_only=True)
class Attendee(ABC):
    """Attendee base class. All format specific attendee classes should derive from this"""

    name: str
    email: str
    attendance_registered: bool | None = False


@dataclass(kw_only=True)
class ButterAttendee(Attendee):
    session_duration: float


@dataclass(kw_only=True)
class ArloRegistration(Attendee):
    reg_href: str

    def __eq__(self, other):
        if not isinstance(other, Attendee):
            return NotImplemented

        if isinstance(other, ButterAttendee):
            return (
                self.name.lower() == other.name.lower()
                or self.email.lower() == other.email.lower()
            )
        else:
            return NotImplemented


@dataclass
class Meeting:
    event_code: str
    start_date: datetime
    attendees: list[Attendee]


class AttendanceStatus(Enum):
    ATTENDED = "Attended"
    DID_NOT_ATTEND = "DidNotAttend"
    UNKNOWN = "Unknown"
