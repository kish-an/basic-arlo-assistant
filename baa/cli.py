import click
import os
from pathlib import Path


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
@click.argument("attendee_file", type=click.Path(exists=True))
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
def main(attendee_file: Path, format: str, platform: str) -> None:
    """Automate registering attendees on Arlo from a virtual meeting platforms attendance report (ATTENDEE_FILE). See --format for the supported platforms"""
    click.echo(f"{banner()}\n\n")

    if "ARLO_USER" not in os.environ or "ARLO_PASS" not in os.environ:
        click.secho(
            "Please enter your Arlo credentials. These are only used to authenticate to the Arlo API.",
            fg="yellow",
        )
    username: str = os.getenv("ARLO_USER") or click.prompt("Username")
    password: str = os.getenv("ARLO_PASS") or click.prompt("Password", hide_input=True)


if __name__ == "__main__":
    main()
