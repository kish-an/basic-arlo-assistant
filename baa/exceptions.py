class CourseCodeNotFound(Exception):
    """
    Exception for missing course code.

    Raised when an attendance report is parsed and no course code can be found. This exception is also raised if the supplied course code does not correspond to any Arlo events.
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
