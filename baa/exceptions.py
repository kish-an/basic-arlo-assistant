class EventNotFound(Exception):
    """
    Exception for not being able to find a valid Arlo Event.

    Raised when an attendee file is parsed and no event code can be found. This exception is also raised if the supplied event code does not correspond to any Arlo events.
    """


class SessionNotFound(Exception):
    """
    Exception for not being able to find a valid Arlo Event Session.

    Raised when an attendee file is parsed and no sessions match the date. This exception is also raised if the supplied date does not correspond to any Arlo Event Sessions.
    """


class CredentialsNotFound(Exception):
    """
    Exception for missing keyring credentials.

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


class AttendeeFileProcessingError(Exception):
    """
    Exception for issues encountered while processing the attendee file.

    Raised when the attendee file is not in the expected format,
    or when there are errors during the parsing of its contents.
    """
