import click
import sys
from pathlib import Path
from datetime import datetime

from baa.main import baa
from baa.helpers import (
    banner,
    has_keyring_credentials,
    get_keyring_name,
    set_keyring_credentials,
)
from baa.exceptions import (
    EventNotFound,
    AuthenticationFailed,
    ApiCommunicationFailure,
    AttendeeFileProcessingError,
)


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("attendee_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "-f",
    "--format",
    default="butter",
    type=click.Choice(["butter"], case_sensitive=False),
    help="The format of the ATTENDEE_FILE. Most virtual meeting platforms allow generating attendance reports in various formats",
)
@click.option(
    "-p",
    "--platform",
    default="codefirstgirls",
    help="Subdomain of the Arlo platform to use for signing into the management system",
)
@click.option(
    "-c",
    "--event-code",
    help="Unique code identifying the Arlo event. Required if it cannot be automatically parsed from the ATTENDEE_FILEE",
)
@click.option(
    "-d",
    "--date",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    help="Date of the meeting in YYYY-MM-DD format. Required if it cannot be automatically parsed from the ATTENDEE_FILE",
)
@click.option(
    "--min-duration",
    type=int,
    default=0,
    help="Minimum duration (in minutes) for an attendee to be marked as present",
)
@click.option(
    "--skip-absent",
    is_flag=True,
    default=False,
    help="If flag is set, only update attendance for present attendees in ATTENDEE_FILE. Absent attendees will not be updated",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Simulate changes to be made without updating any registration records. ",
)
def main(
    attendee_file: Path,
    format: str,
    platform: str,
    event_code: str | None,
    date: datetime | None,
    min_duration: int,
    skip_absent: bool,
    dry_run: bool,
) -> None:
    """Automate registering attendees in Arlo with attendance reports from virtual meeting platforms (ATTENDEE_FILE). See --format for supported platforms"""
    click.echo(banner())

    if not has_keyring_credentials():
        click.secho(
            f"Please enter your Arlo login details, these are solely used to authenticate to the Arlo API. The credentials will be securely stored in your systems keyring service ({get_keyring_name()})",
            fg="yellow",
        )
        set_keyring_credentials()

    try:
        baa(
            attendee_file,
            format,
            platform,
            event_code,
            date,
            min_duration,
            skip_absent,
            dry_run,
        )
    except (
        EventNotFound,
        AuthenticationFailed,
        ApiCommunicationFailure,
        AttendeeFileProcessingError,
    ) as e:
        click.secho(e, fg="red")
        sys.exit(1)


if __name__ == "__main__":
    main()
