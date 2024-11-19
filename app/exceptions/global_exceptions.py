"""Global exception handlers for API endpoints."""

from fastapi import HTTPException


class DataNotFoundException(HTTPException):

    """
    Exception for when data is not found.

    :param detail: The detail message for the exception.
    :type detail: str, optional
    :returns: A DataNotFoundException object.

    """

    def __init__(self, detail: str = "Data not found"):
        """
        Initialize the DataNotFoundException object.

        :param detail:
        :type detail:
        :returns:
        """
        super().__init__(status_code=404, detail=detail)

class InvalidIdentifier(HTTPException):

    """
    Exception for when data is not found.

    :param detail: The detail message for the exception.
    :type detail: str, optional
    :returns: A DataNotFoundException object.

    """

    def __init__(self, detail: str = "Data not found"):
        """
        Initialize the DataNotFoundException object.

        :param detail:
        :type detail:
        :returns:
        """
        super().__init__(status_code=400, detail=detail)
