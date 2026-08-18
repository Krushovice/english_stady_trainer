class DomainError(Exception):
    """Base class for expected, user-facing domain errors."""


class AlreadyExistsError(DomainError):
    pass


class InvalidCredentialsError(DomainError):
    pass


class NotAuthenticatedError(DomainError):
    pass


class NotFoundError(DomainError):
    pass


class AIProviderUnavailableError(DomainError):
    """Raised when the configured AI provider can't be reached.

    AI features must degrade gracefully instead of crashing — the rest of the
    platform (lessons, exercises, mistakes, review) never depends on AI.
    """


class AIResponseParsingError(DomainError):
    """Raised when the AI provider responded, but not in the expected shape."""


class ConversationEndedError(DomainError):
    """Raised when trying to send a message to a conversation that already ended."""


class STTProviderUnavailableError(DomainError):
    """Raised when the configured speech-to-text provider can't be reached.

    Same graceful-degradation contract as AIProviderUnavailableError, kept as
    a distinct type since Speaking depends on a second, independent vendor —
    text AI being up says nothing about STT being up, and vice versa.
    """
