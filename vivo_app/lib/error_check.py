"""Defines the deliberate error raised by the error-check endpoint."""


class IntentionalErrorCheckError(RuntimeError):
    """Signals that the development-only error-check endpoint was requested."""
