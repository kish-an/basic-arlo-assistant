import click
import os
from pathlib import Path
from typing import Optional

from baa.main import baa


def banner() -> str:
    banner = [
        "         __  _                            ",
        "      .-.'  `; `-._  __  _                ",
        "      (_,         .-:'  `; `-._           ",
        "    ,'o\"(        (_,           )         ",
        "   (__,-'      ,'o\"(            )>       ",
        "      (       (__,-'            )         ",
        "       `-'._.--._(             )          ",
        "          |||  |||`-'._.--._.-'           ",
        "                     |||  |||             ",
        "                                          ",
        "        Basic Arlo Assistant              ",
    ]
    return "\n".join(line.center(os.get_terminal_size().columns) for line in banner)


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("attendee_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "-f",
    "--format",
    default="butter",
    help="The format of the ATTENDEE_FILE. Most virtual meeting platforms provide functionality to generate an attendance report",
    type=click.Choice(["butter"], case_sensitive=False),
)
@click.option(
    "--platform",
    default="codefirstgirls",
    help="The Arlo platform subdomain to use. This will be the first segment used to sign into the Arlo management system: {subdomain}.arlo.co",
)
@click.option(
    "--course-code",
    help="The course code to identify the Arlo event. This is only required if this is not included in the ATTENDEE_FILE",
)
def main(
    attendee_file: Path, format: str, platform: str, course_code: Optional[str]
) -> None:
    """Automate registering attendees on Arlo from a virtual meeting platforms attendance report (ATTENDEE_FILE). See --format for the supported platforms"""
    click.echo(f"{banner()}\n\n")

    if "ARLO_USER" not in os.environ or "ARLO_PASS" not in os.environ:
        click.secho(
            "Please enter your Arlo credentials. These are solely used to authenticate to the Arlo API.",
            fg="yellow",
        )
    username: str = os.getenv("ARLO_USER") or click.prompt("Username")
    password: str = os.getenv("ARLO_PASS") or click.prompt("Password", hide_input=True)

    baa(attendee_file, format, platform, course_code, username, password)


if __name__ == "__main__":
    main()
