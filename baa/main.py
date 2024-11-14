import logging
import asyncio
from pathlib import Path
import click
from prettytable import PrettyTable
from datetime import datetime
from timeit import default_timer as timer

from baa.attendee_parser import butter
from baa.arlo_api import ArloClient
from baa.classes import AttendanceStatus, Attendee, ArloRegistration, Meeting
from baa.helpers import LoadingSpinner

logger = logging.getLogger(__name__)


def notify_unregistered_attendees(
    attendee_list: list[Attendee], min_duration: int, skip_absent: bool
) -> None:
    click.secho(
        f"⚠️  The following attendees could not be found in Arlo{', or they did not exceed the --min-duration threshold.' if min_duration > 0 else ''} {'They have been marked as did not attend!' if not skip_absent else ''} Follow up to confirm attendance",
        fg="yellow",
    )
    unregistered_table = PrettyTable(
        field_names=["Name", "Email", "Duration (minutes)"]
    )
    unregistered_table.align = "l"
    for attendee in attendee_list:
        unregistered_table.add_row(
            [
                attendee.name,
                attendee.email,
                click.style(
                    attendee.session_duration,
                    fg=("red" if attendee.session_duration < min_duration else "reset"),
                ),
            ]
        )
    click.echo(f"{unregistered_table.get_string(sortby='Name')}")


def create_registered_table(registrations: list[ArloRegistration]) -> PrettyTable:
    registered_table = PrettyTable(
        field_names=["Name", "Email", "Attendance registered"]
    )
    registered_table.align["Name"] = "l"
    registered_table.align["Email"] = "l"
    registered_table.align["Attendance registered"] = "c"

    for reg in registrations:
        status_icon = {True: "✅", False: "❌", None: "⚠️"}.get(
            reg.attendance_registered
        )
        registered_table.add_row([reg.name, reg.email, status_icon])

    return registered_table


async def update_attendance(arlo_client: ArloClient, reg: ArloRegistration) -> None:
    attendance_status = (
        AttendanceStatus.ATTENDED
        if reg.attendance_registered
        else AttendanceStatus.DID_NOT_ATTEND
    )
    logger.debug(f"Updating attendance for {reg} to {attendance_status}")

    update_success = await arlo_client.update_attendance(
        reg.reg_href, attendance_status
    )
    if not update_success:
        click.secho(
            f"⚠️  Unable to update attendance for {reg.name}: {reg.email}",
            fg="yellow",
        )
        reg.attendance_registered = None


async def process_registrations(
    arlo_client: ArloClient,
    meeting: Meeting,
    event_code: str | None,
    session_date: datetime | None,
    min_duration: int,
    skip_absent: bool,
    dry_run: bool,
) -> list[ArloRegistration]:
    registrations = []
    updates = []
    for reg in arlo_client.get_registrations(event_code, session_date):
        # Check if registration matches any meeting attendees
        if reg in meeting.attendees:
            attendee = meeting.attendees[meeting.attendees.index(reg)]
            logger.debug(f"Match found in Arlo for {attendee}")

            if attendee.session_duration >= min_duration:
                attendee.attendance_registered = True
                reg.attendance_registered = True
            else:
                logger.debug(
                    f"Did not meet minimum duration threshold of{min_duration} mins"
                )

        # Skip absent registrations if flag is set
        if skip_absent and not reg.attendance_registered:
            continue

        registrations.append(reg)

        if not dry_run:
            updates.append(update_attendance(arlo_client, reg))

    await asyncio.gather(*updates, return_exceptions=True)
    return registrations


async def baa(
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
    start = timer()

    try:
        arlo_client = ArloClient(platform)
        meeting = butter.get_attendees(attendee_file, event_code)
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

        loading_msg = (
            "Updating Arlo registrations"
            if not dry_run
            else "Loading Arlo registrations (no records will be updated)"
        )
        with LoadingSpinner(loading_msg):
            registrations = await process_registrations(
                arlo_client,
                meeting,
                event_code,
                session_date,
                min_duration,
                skip_absent,
                dry_run,
            )

        end = timer()
        logger.debug(f"Elapsed time to update registrations was {end - start} seconds")

        if registrations:
            registered_table = create_registered_table(registrations)
            click.echo(registered_table.get_string(sortby="Name") + "\n")

        unregistered_attendees = [
            atnd for atnd in meeting.attendees if not atnd.attendance_registered
        ]
        if unregistered_attendees:
            notify_unregistered_attendees(
                unregistered_attendees,
                min_duration,
                skip_absent,
            )
    finally:
        await arlo_client.close()
