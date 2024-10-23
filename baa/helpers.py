import base64
import click
import os
import keyring
from threading import Thread
from itertools import cycle
import time
from typing import Tuple, Optional, List

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
    return "\n".join(line.center(os.get_terminal_size().columns) for line in BAA_BANNER)


def b64encode_str(msg: str, encoding="utf-8") -> str:
    msg_bytes = msg.encode(encoding)
    base64_bytes = base64.b64encode(msg_bytes)
    return base64_bytes.decode(encoding)


def b64decode_str(msg: str, encoding="utf-8") -> str:
    base64_bytes = msg.encode(encoding)
    msg_bytes = base64.b64decode(base64_bytes)
    return msg_bytes.decode(encoding)


def has_keyring_credentials() -> bool:
    return keyring.get_password(BAA_KEYRING_DOMAIN, BAA_KEYRING_USER) is not None


def set_keyring_credentials() -> None:
    keyring.set_password(
        BAA_KEYRING_DOMAIN,
        BAA_KEYRING_USER,
        f"{b64encode_str(click.prompt('Username'))};{b64encode_str(click.prompt('Password', hide_input=True, confirmation_prompt=True))}",
    )


def get_keyring_name() -> str:
    return keyring.get_keyring().name


def get_keyring_credentials() -> Optional[Tuple[str, str]]:
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
    keyring.delete_password(BAA_KEYRING_DOMAIN, BAA_KEYRING_USER)


class LoadingSpinner:
    def __init__(
        self,
        msg: str = "Loading..",
        colour: str = "blue",
        icons: List[str] = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"],
    ):
        self.msg = msg
        self.colour = colour
        self.icons = cycle(icons)
        self.loading = False
        self.thread = Thread(target=self._spin)

    def _spin(self) -> None:
        while self.loading:
            click.secho(f"\r{self.msg} {next(self.icons)}", fg=self.colour, nl=False)
            time.sleep(0.1)

    def start(self) -> None:
        self.loading = True
        self.thread.start()

    def stop(self) -> None:
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
