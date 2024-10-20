import base64
import click
import os
import keyring
from typing import Tuple, Optional


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
    "       🐏 Basic Arlo Assistant 🐑          ",
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


def get_keyring_credentials() -> Optional[Tuple[str, str]]:
    if not has_keyring_credentials():
        return None

    return tuple(
        map(
            b64decode_str,
            keyring.get_password(BAA_KEYRING_DOMAIN, BAA_KEYRING_USER).split(";"),
        )
    )

def remove_keyring_credentials() -> None:
    keyring.delete_password(BAA_KEYRING_DOMAIN, BAA_KEYRING_USER)
