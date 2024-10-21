import click
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

from baa.main import baa
from baa.helpers import banner, has_keyring_credentials, get_keyring_name, set_keyring_credentials
from baa.exceptions import (
    CourseCodeNotFound,
    AuthenticationFailed,
    ApiCommunicationFailure,
)


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("attendee_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "-f",
    "--format",
    default="butter",
    type=click.Choice(["butter"], case_sensitive=False),
    help="The format of the ATTENDEE_FILE. Most virtual meeting platforms provide functionality to generate an attendance report",
)
@click.option(
    "--platform",
    default="codefirstgirls",
    help="The Arlo platform subdomain to use. This will be the first segment used to sign into the Arlo management system: {subdomain}.arlo.co",
)
@click.option(
    "--event-code",
    help="The event code to identify the Arlo event. This is only required if it can not be parsed from ATTENDEE_FILE",
)
@click.option(
    "--date",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    help="The date of the meeting in YYYY/MM/DD format to identify the Arlo session. This is only required if it can not be parsed from ATTENDEE_FILE",
)
@click.option(
    "--skip-absent",
    is_flag=True,
    default=True,
    help="Only update attendance for any matches in ATTENDEE_FILE. The default behaviour will mark any absent attendees as did not attend",
)
def main(
    attendee_file: Path,
    format: str,
    platform: str,
    event_code: Optional[str],
    date: Optional[datetime],
    skip_absent: bool,
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
        baa(attendee_file, format, platform, event_code, date, skip_absent)
    except (
        CourseCodeNotFound,
        AuthenticationFailed,
        ApiCommunicationFailure,
    ) as e:
        click.secho(e, fg="red")
        sys.exit(1)


if __name__ == "__main__":
    main()
