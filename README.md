# Basic Arlo Assistant
```
              ██████████████████
            ██                  ██
          ██                      ██
        ██                          ██      ████████      ██████▓▓██
        ██  ░░██████████████          ██████        ██████          ████
      ██    ██░░░░░░░░░░░░░░██                                          ██
    ████  ██░░░░░░░░░░░░░░░░░░██    ██                                    ██
  ██░░░░██░░░░░░██░░░░██░░░░░░██  ██░░██▒▒                                  ██
    ██████░░░░░░██░░░░██░░░░░░██  ██░░░░▒▒██                                  ██
        ██░░░░░░░░░░░░░░░░░░░░██    ████▓▓                                      ██
      ██  ░░░░░░░░░░░░░░░░░░░░██                                                ██
      ██░░░░░░░░░░░░░░░░░░░░░░██                                                ██
    ██░░░░░░░░░░░░░░░░░░░░░░██                                                  ██
    ██░░▓▓▓▓▓▓▓▓░░░░░░░░░░██                                                    ██
    ██░░░░▓▓▓▓░░░░░░░░░░██      ░░                              ░░              ██
      ██░░░░░░░░▒▒░░▒▒██░░░░  ░░    ░░  ░░░░      ░░        ░░  ░░              ██
      ██░░░░░░░░▒▒░░▒▒██  ░░  ░░        ░░    ░░░░░░  ░░        ░░░░            ██
        ██████████▓▓▓▓░░░░░░  ░░    ░░  ░░      ░░░░  ░░        ░░░░            ██
                  ██▓▓░░                                                        ██
                  ██▓▓░░                                                        ██
                      ██░░                                                    ░░██
                      ██░░                            ░░                    ░░██
                    ░░██░░░░                                            ░░░░░░██
                        ██░░░░░░░░░░░░░░░░░░    ░░░░░░░░░░░░        ░░░░██████
                          ██░░██░░░░░░██▓▓░░░░░░██████████░░░░░░░░██████░░██
                            ██▒▒██████░░▒▒██████          ██████▓▓██  ██░░██
                            ██░░██  ██░░░░██                ██▒▒▒▒██  ██░░██
                            ██░░██  ██░░▒▒██                ██░░▒▒██  ██░░██
                            ██░░██  ██░░░░██                ██░░▒▒██  ██░░██
                            ██░░██  ██░░░░██                ██░░▒▒██  ██░░██
                            ██████  ████████                ████▓▓██  ██████
                            ██▒▒██  ██▒▒▒▒██                ██▒▒▒▒██  ██▒▒██
```
Automate attendance registration in [Arlo](https://www.arlo.co/) with attendance reports from virtual meeting platforms.

## Getting Started

> [!IMPORTANT]
> This tool is in early development and may introduce breaking changes with new releases. Although the tool has been tested, there may be edge cases that have not been accounted for. Please exercise due diligence when using this tool for attendance registration.

### Prerequisites
- Python 3.10+
- Arlo [API role](https://support.arlo.co/hc/en-gb/articles/360018341612-Manage-your-users-access#:~:text=API%20role)

### Installation

Installation with [pipx](https://pipx.pypa.io/stable/) is strongly recommended, this provides an isolated environment for baa and it's depdendencies. See the [Python Packaging User Guide](https://packaging.python.org/en/latest/guides/installing-stand-alone-command-line-tools/) for more information on installing command line tools with pipx.

```sh
pipx install baa
```

Alternatively, baa can be installed with pip.

> [!TIP]
> Use `pip install --user` if you do not have administrative privileges, or want to avoid affecting other users on your system. This will install packages for the current user, rather than the default system-wide directory.

```sh
pip install baa
```

## Usage

View the available options that baa supports

```sh
baa -h
```

The attendance report (see [supported platforms](#supported-platforms)) must be provided. By default, baa will try to find a match for each attendee in Arlo and mark them as attended. All other registrations for the session will be marked as did not attend.

```sh
baa path/to/attendance-report.csv
```

## Supported Platforms

- [Butter](https://www.butter.us/):  The attendance report can be downloaded by opening the recap for the session. Under the **Engagement** tab, select **People** and then **Download list**. This will require the Collaborator role on the Butter room.

## Contributing

Contributions are welcome! If you encounter any issues or have suggestions for improvements, please open an issue or submit a pull request.
