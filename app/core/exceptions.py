class DomainError(Exception):
    """Base class for expected, user-facing domain errors."""


class AlreadyExistsError(DomainError):
    pass


class InvalidCredentialsError(DomainError):
    pass


class NotAuthenticatedError(DomainError):
    pass
