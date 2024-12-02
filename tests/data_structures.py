"""Custom classes used in testing."""


class ImmutableDict(dict):
    """Implements an immutable dictionary for safely using dictionary fixtures."""

    def __init__(self, *args, **kwargs):
        """Pass through to parent constructor nothing fancy here."""
        super().__init__(*args, **kwargs)

    def __setitem__(self, key, value):
        """Remove item assignment."""
        raise TypeError("ImmutableDict does not support item assignment")

    def __delitem__(self, key):
        """Remove item deletion."""
        raise TypeError("ImmutableDict does not support item deletion")
