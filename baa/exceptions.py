class CourseCodeNotFound(Exception):
    """
    Exception for missing course code.

    Raised when an attendance report is parsed and no course code can be found. Or if the selected format doesn't support it and no course code was supplied.
    """
