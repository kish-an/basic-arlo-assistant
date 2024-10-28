import base64
import click
import os
import keyring
from threading import Thread
from itertools import cycle
import time

from baa.exceptions import CredentialsNotFound


BAA_BANNER = [
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
    "       🐑 Basic Arlo Assistant 🐑          ",
]

BAA_KEYRING_DOMAIN = "Basic Arlo Assistant"
BAA_KEYRING_USER = "Arlo Credentials"


def banner() -> str:
    """Generate a centered banner for Basic Arlo Assistant."""
    return "\n".join(line.center(os.get_terminal_size().columns) for line in BAA_BANNER)


def b64encode_str(msg: str, encoding: str = "utf-8") -> str:
    """
    Encode a string to Base64.

    Args:
        msg (str): The string to encode.
        encoding (str, optional): The character encoding to use. Defaults to "utf-8".

    Returns:
        str: Base64 encoded string.
    """
    msg_bytes = msg.encode(encoding)
    base64_bytes = base64.b64encode(msg_bytes)
    return base64_bytes.decode(encoding)


def b64decode_str(msg: str, encoding: str = "utf-8") -> str:
    """
    Decode a Base64 encoded string.

    Args:
        msg (str): The Base64 string to decode.
        encoding (str, optional): The character encoding to use. Defaults to "utf-8".

    Returns:
        str: Decoded string.
    """
    base64_bytes = msg.encode(encoding)
    msg_bytes = base64.b64decode(base64_bytes)
    return msg_bytes.decode(encoding)


def has_keyring_credentials() -> bool:
    """Check if credentials exist in the keyring."""
    return keyring.get_password(BAA_KEYRING_DOMAIN, BAA_KEYRING_USER) is not None


def set_keyring_credentials() -> None:
    """Prompt the user for credentials and store them in the keyring."""
    keyring.set_password(
        BAA_KEYRING_DOMAIN,
        BAA_KEYRING_USER,
        f"{b64encode_str(click.prompt('Username'))};{b64encode_str(click.prompt('Password', hide_input=True, confirmation_prompt=True))}",
    )


def get_keyring_name() -> str:
    """Get the current keyring name."""
    return keyring.get_keyring().name


def get_keyring_credentials() -> tuple[str, str]:
    """
    Retrieve and decode credentials from the keyring.

    Raises:
        CredentialsNotFound: If no credentials are found in the keyring.

    Returns:
        tuple[str, str]: A tuple containing the username and password for the Arlo platform.
    """
    if not has_keyring_credentials():
        raise CredentialsNotFound(
            f"🚨 Could not find Arlo credentials in the keyring service ({get_keyring_name()})"
        )

    return tuple(
        map(
            b64decode_str,
            keyring.get_password(BAA_KEYRING_DOMAIN, BAA_KEYRING_USER).split(";"),
        )
    )


def remove_keyring_credentials() -> None:
    """Remove stored credentials from the keyring."""
    keyring.delete_password(BAA_KEYRING_DOMAIN, BAA_KEYRING_USER)


class LoadingSpinner:
    """A simple loading spinner for indicating progress in the console."""
    def __init__(
        self,
        msg: str = "Loading",
        colour: str = "blue",
        icons: list[str] = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"],
    ):
        """Initialize the loading spinner.

        Args:
            msg (str, optional): The message to display with the spinner. Defaults to "Loading".
            colour (str, optional): The color of the spinner. Defaults to "blue".
            icons (list[str], optional): The icons to cycle through for the spinner. Defaults to a predefined list.
        """
        self.msg = msg
        self.colour = colour
        self.icons = cycle(icons)
        self.loading = False
        self.thread = Thread(target=self._spin)

    def _spin(self) -> None:
        """Run the spinner animation in a separate thread."""
        while self.loading:
            click.secho(f"\r{self.msg} {next(self.icons)}", fg=self.colour, nl=False)
            time.sleep(0.1)

    def start(self) -> None:
        """Start the spinner thread."""
        self.loading = True
        self.thread.start()

    def stop(self) -> None:
        """Stop the spinner thread."""
        # Move stdout to new line
        click.echo()
        self.loading = False
        self.thread.join()

    # Methods to support with statement (cleans up spinner in case an exception is hit)
    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()
