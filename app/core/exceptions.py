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


class SpeakingAttemptAlreadySubmittedError(DomainError):
    """Raised when submitting audio to a speaking attempt that already has one."""


class EmptyTranscriptError(DomainError):
    """Raised when STT returns no usable speech (silence, noise-only audio)."""


class LevelLockedError(DomainError):
    """Raised when accessing a level whose prerequisite exit exam isn't passed yet."""


class LessonLockedError(DomainError):
    """Raised when accessing a lesson whose preceding lesson in the level isn't passed yet."""


class ExamAlreadyPassedError(DomainError):
    """Raised when starting a new attempt at an exam already passed."""


class ExamOnCooldownError(DomainError):
    """Raised when starting a new attempt while the 3-attempts-in-a-row cooldown is active."""

    def __init__(self, message: str, *, retry_at: object) -> None:
        super().__init__(message)
        self.retry_at = retry_at


class ExamAttemptNotFoundError(DomainError):
    """Raised when submitting to an exam attempt that doesn't exist or isn't the user's."""


class ExamAttemptAlreadySubmittedError(DomainError):
    """Raised when submitting an exam attempt that was already graded."""
