"""
ophix_conf.validators.base
~~~~~~~~~~~~~~~~~~~~~~~~~~
Base validator interface for configuration format validators.
"""

from django.core.exceptions import ValidationError


class BaseValidator:
    """
    Base class for all configuration format validators.

    Subclasses must implement ``validate(content: str) -> None``.
    Raise ``django.core.exceptions.ValidationError`` if the content
    is invalid for this format.
    """

    def validate(self, content: str) -> None:
        """
        Validate *content* for this format.

        Parameters
        ----------
        content
            The raw configuration content string to validate.

        Raises
        ------
        django.core.exceptions.ValidationError
            If the content is not valid for this format.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement validate()"
        )
