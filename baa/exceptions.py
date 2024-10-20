class CourseCodeNotFound(Exception):
    """
    Exception for missing course code.

    Raised when an attendance report is parsed and no course code can be found. This exception is also raised if the supplied course code does not correspond to any Arlo events.
    """


class SessionNotFound(Exception):
    """
    Exception for missing session.

    Raised when there are no sessions matching the provided date parsed from the attendance report.
    """


class CredentialsNotFound(Exception):
    """
    Exception for missing credentials.

    Raised when get_keyring_credentials is called, which always expects to fetch credentials from the keyring service, and there is no valid entry.
    """


class AuthenticationFailed(Exception):
    """
    Exception for failing to autenticate to the Arlo API.

    Raised when making a request to the Arlo API, and the response HTTP code is 403.
    """


class ApiCommunicationFailure(Exception):
    """
    Exception for not being able to connect to the Arlo API.

    Raised when making a request to the Arlo API, and the response HTTP code is not 200.
    """
