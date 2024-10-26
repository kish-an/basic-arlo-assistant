import pytest
from click.testing import CliRunner
from datetime import datetime

from baa.cli import main
from baa.exceptions import AuthenticationFailed


@pytest.fixture
def cli_runner(mocker):
    mocker.patch("baa.cli.baa")
    # Mock banner as call to get_terminal_size() wont work in CliRunner
    mocker.patch("baa.cli.banner", return_value="")
    return CliRunner()


@pytest.fixture(autouse=True)
def mock_keyring(mocker):
    mocker.patch("baa.cli.has_keyring_credentials", return_value=True)
    mocker.patch("baa.cli.set_keyring_credentials")


@pytest.fixture
def attendee_file(tmp_path):
    attendee_file = tmp_path / "attendee_file.csv"
    attendee_file.write_text("temp", encoding="utf-8")
    return attendee_file


def test_cli_success(cli_runner, attendee_file, mocker):
    mock_baa = mocker.patch("baa.cli.baa")

    result = cli_runner.invoke(
        main,
        [attendee_file.as_posix()],
    )
    print(result.output)
    assert result.exit_code == 0
    mock_baa.assert_called_once_with(
        attendee_file, "butter", "codefirstgirls", None, None, 0, False, False
    )


def test_cli_invalid_attendee_file(cli_runner):
    result = cli_runner.invoke(main, ["invalid_file.csv"])
    assert result.exit_code != 0
    assert "Invalid value for 'ATTENDEE_FILE'" in result.output


def test_cli_with_options(cli_runner, attendee_file, mocker):
    mock_baa = mocker.patch("baa.cli.baa")

    result = cli_runner.invoke(
        main,
        [
            attendee_file.as_posix(),
            "--format",
            "butter",
            "--platform",
            "myplatform",
            "--event-code",
            "CK24ABC",
            "--date",
            "2024-01-01",
            "--min-duration",
            "90",
            "--skip-absent",
            "--dry-run",
        ],
    )

    assert result.exit_code == 0
    mock_baa.assert_called_once_with(
        attendee_file,
        "butter",
        "myplatform",
        "CK24ABC",
        datetime(2024, 1, 1),
        90,
        True,
        True,
    )


def test_cli_no_keyring_credentials(cli_runner, attendee_file, mocker):
    mocker.patch("baa.cli.has_keyring_credentials", return_value=False)
    mock_set_password = mocker.patch("baa.cli.set_keyring_credentials")

    result = cli_runner.invoke(main, [attendee_file.as_posix()])

    assert result.exit_code == 0
    mock_set_password.assert_called_once()


def test_cli_auth_failed(cli_runner, attendee_file, mocker):
    mocker.patch(
        "baa.cli.baa", side_effect=AuthenticationFailed("Authentication failed")
    )

    result = cli_runner.invoke(main, [attendee_file.as_posix()])

    assert result.exit_code == 1
    assert "Authentication failed" in result.output
