import logging
from pathlib import Path
import click
from prettytable import PrettyTable
from datetime import datetime

from baa.attendee_parser import butter
from baa.arlo_api import ArloClient
from baa.classes import AttendanceStatus
from baa.helpers import LoadingSpinner

logger = logging.getLogger(__name__)


def baa(
    attendee_file: Path,
    format: str,
    platform: str,
    event_code: str | None,
    date: datetime | None,
    min_duration: int,
    skip_absent: bool,
    dry_run: bool,
) -> None:
    """
    Update Arlo attendance records based on attendees from the provided attendee file.

    This function matches registrations in Arlo with attendees from the specified file, updating their attendance status according to criteria like minimum session duration and skipping absent registrations. Can also be used in a dry-run mode where the process is simulated but no updates are made.
    """
    logger.info(f"Processing attendees in {attendee_file}")

    meeting = butter.get_attendees(attendee_file, event_code)
    arlo_client = ArloClient(platform)
    event_code = event_code or meeting.event_code
    session_date = date or meeting.start_date

    click.echo(
        click.style("Event: ", fg="green", bold=True)
        + click.style(arlo_client.get_event_name(event_code), fg="green")
    )
    click.echo(
        click.style("Session: ", fg="green", bold=True)
        + click.style(
            arlo_client.get_session_name(event_code, session_date), fg="green"
        )
        + "\n"
    )

    registered_table = PrettyTable(
        field_names=["Name", "Email", "Attendance registered"]
    )
    registered_table.align["Name"] = "l"
    registered_table.align["Email"] = "l"
    registered_table.align["Attendance registered"] = "c"

    loading_msg = (
        "Updating Arlo registrations"
        if not dry_run
        else "Loading Arlo registrations (no records will be updated)"
    )
    with LoadingSpinner(loading_msg):
        for reg in arlo_client.get_registrations(event_code, session_date):
            # Check if registration matches any meeting attendees
            if reg in meeting.attendees:
                attendee = meeting.attendees[meeting.attendees.index(reg)]
                logger.debug(f"Match found in Arlo for {attendee}")

                if attendee.session_duration < min_duration:
                    logger.debug(
                        f"Attendee did not meet minimum duration threshold {min_duration} mins: {attendee}"
                    )
                    continue

                attendee.attendance_registered = True
                reg.attendance_registered = True

            # Skip absent registrations if flag is set
            if skip_absent and not reg.attendance_registered:
                continue

            if not dry_run:
                logger.debug(f"Updating attendance for {reg}")
                update_success = arlo_client.update_attendance(
                    reg.reg_href,
                    (
                        AttendanceStatus.ATTENDED
                        if reg.attendance_registered
                        else AttendanceStatus.DID_NOT_ATTEND
                    ),
                )
                if not update_success:
                    click.secho(
                        f"⚠️  Unable to update attendance for {reg.name}: {reg.email}",
                        fg="yellow",
                    )
                    reg.attendance_registered = None

            status_icon = {True: "✅", False: "❌", None: "⚠️"}.get(
                reg.attendance_registered
            )
            registered_table.add_row([reg.name, reg.email, status_icon])

    if registered_table.rows:
        click.echo(f"{registered_table.get_string(sortby='Name')}\n")

    unregistered_attendees = [
        a for a in meeting.attendees if not a.attendance_registered
    ]
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
                        fg=(
                            "red"
                            if attendee.session_duration < min_duration
                            else "reset"
                        ),
                    ),
                ]
            )
        click.echo(f"{unregistered_table.get_string(sortby='Name')}")
