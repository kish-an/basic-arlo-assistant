from pathlib import Path
import click
from prettytable import PrettyTable
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
    min_duration: int,
    skip_absent: bool,
    dry_run: bool,
) -> None:
    meeting = butter.get_attendees(attendee_file, event_code)
    arlo_client = ArloClient(platform)

    registered_table = PrettyTable(
        field_names=["Name", "Email", "Attendance registered"]
    )
    registered_table.align = "l"

    for reg in arlo_client.get_registrations(
        event_code=event_code or meeting.event_code,
        session_date=date or meeting.start_date,
    ):
        #  Check if registration matches any meeting attendees
        if reg in meeting.attendees:
            attendee = meeting.attendees[meeting.attendees.index(reg)]
            if attendee.session_duration > min_duration:
                attendee.attendance_registered = True
                reg.attendance_registered = True

        # Skip absent registrations if flag is set
        if skip_absent and not reg.attendance_registered:
            continue

        if not dry_run:
            update_success = arlo_client.update_attendance(
                reg.reg_href,
                (
                    Attendance.ATTENDED
                    if reg.attendance_registered
                    else Attendance.DID_NOT_ATTEND
                ),
            )
            if not update_success:
                click.secho(
                    f"⚠️  Unable to update attendance for {reg.name}: {reg.email})",
                    fg="yellow",
                )
                reg.attendance_registered = None

        registered_table.add_row(
            [
                reg.name,
                reg.email,
                (
                    "✅"
                    if reg.attendance_registered
                    else "⚠️" if reg.attendance_registered is None else "❌"
                ),
            ]
        )

    if len(registered_table.rows) > 0:
        click.echo(f"{registered_table.get_string(sortby='Name')}\n")

    unregistered_attendees = list(
        filter(lambda a: not a.attendance_registered, meeting.attendees)
    )
    if len(unregistered_attendees) > 0:
        click.secho(
            f"⚠️  The following attendees could not be found in Arlo{', or they did not exceed the --min-duration threshold.' if min_duration > 0 else ''} {'They have been marked as did not attend!' if not skip_absent else ''} Follow up to confirm attendance",
            fg="yellow",
        )
        unregistered_table = PrettyTable(
            field_names=["Name", "Email", "Duration (minutes)"]
        )
        unregistered_table.align = "l"
        for attendee in unregistered_attendees:
            unregistered_table.add_row(
                [
                    attendee.name,
                    attendee.email,
                    click.style(
                        attendee.session_duration,
                        fg="red" if attendee.session_duration < min_duration else "reset",
                    ),
                ]
            )
        click.echo(f"{unregistered_table.get_string(sortby='Name')}")
