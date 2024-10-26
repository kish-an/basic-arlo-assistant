import pytest
from baa.helpers import (
    b64encode_str,
    b64decode_str,
    has_keyring_credentials,
    get_keyring_credentials,
    set_keyring_credentials,
    remove_keyring_credentials,
    LoadingSpinner,
    BAA_KEYRING_DOMAIN,
    BAA_KEYRING_USER,
)
from baa.exceptions import CredentialsNotFound


def test_base64_encoding_decoding():
    original = "Hello, World!"
    encoded = b64encode_str(original)
    decoded = b64decode_str(encoded)
    assert original == decoded


def test_has_keyring_credentials(mocker):
    mocker.patch("keyring.get_password", return_value="dummy_credentials")
    assert has_keyring_credentials() is True

    mocker.patch("keyring.get_password", return_value=None)
    assert has_keyring_credentials() is False


def test_set_keyring_credentials(mocker):
    mock_set_password = mocker.patch("keyring.set_password")
    mocker.patch("click.prompt", side_effect=["username", "password"])

    set_keyring_credentials()
    mock_set_password.assert_called_once_with(
        BAA_KEYRING_DOMAIN,
        BAA_KEYRING_USER,
        b64encode_str("username") + ";" + b64encode_str("password"),
    )


def test_get_keyring_credentials(mocker):
    username = "username"
    password = "password"
    creds = b64encode_str(username) + ";" + b64encode_str(password)

    mocker.patch("keyring.get_password", return_value=creds)
    assert get_keyring_credentials() == (username, password)


def test_get_keyring_no_credentials(mocker):
    mocker.patch("keyring.get_password", return_value=None)
    with pytest.raises(CredentialsNotFound):
        get_keyring_credentials()


def test_remove_keyring_credentials(mocker):
    mock_delete_password = mocker.patch("keyring.delete_password")
    remove_keyring_credentials()
    mock_delete_password.assert_called_once_with(BAA_KEYRING_DOMAIN, BAA_KEYRING_USER)


@pytest.fixture
def loading_spinner():
    return LoadingSpinner(msg="Testing")


def test_loading_spinner_start(mocker, loading_spinner):
    mock_start = mocker.patch.object(loading_spinner.thread, "start")
    loading_spinner.start()
    assert loading_spinner.loading is True
    mock_start.assert_called_once()


def test_loading_spinner_stop(mocker, loading_spinner):
    mock_join = mocker.patch.object(loading_spinner.thread, "join")
    loading_spinner.stop()
    assert loading_spinner.loading is False
    mock_join.assert_called_once()


def test_loading_spinner_with_context_manager():
    with LoadingSpinner() as spinner:
        assert spinner.loading is True

    assert spinner.loading is False


def test_loading_spinner_thread_join_on_exception(mocker, loading_spinner):
    mock_join = mocker.patch.object(loading_spinner.thread, "join")

    with pytest.raises(Exception):
        with loading_spinner:
            raise Exception("Simulated Exception")

    mock_join.assert_called_once()
