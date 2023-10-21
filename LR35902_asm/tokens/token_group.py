"""Classes that convert text into Tokens."""

# from __future__ import annotations
from collections import OrderedDict
from .token import Token


class TokenGroup:
    """Group a set of tokens related tokens together as a single unit."""

    def __init__(self):
        """Initialize the object."""
        # if primary_token is None:
        #     raise ValueError("The primary_token must have a value.")
        self._group_store = OrderedDict()

    def __repr__(self):
        """Represent this object as a printable string."""
        tokens = self.tokens()
        desc = ""
        for tok in tokens:
            desc += tok.__repr__()
        return desc

    def __str__(self):
        """Format object definition as a printable string."""
        desc = ""
        for idx, tok in enumerate(self.tokens()):
            desc += f"{idx:02d}. {tok.__repr__()}"
        return desc

    def __contains__(self, key):
        """Test if key identifies a Token in the group."""
        return key in self._group_store

    def __getitem__(self, key):
        """Retrieve an individual token by key."""
        if key in self._group_store:
            return self._group_store[key]
        return None

    def __len__(self):
        """Return the number of keys in the dictionary."""
        return len(self._group_store.keys())

    def add(self, token: Token):
        """Add an aditional token to the end of tokens group."""
        if token is None:
            raise ValueError("Passed token must have a value.")
        elif token.directive in self._group_store:
            raise ValueError("Duplicate token directive in group.")

        self._group_store[token.directive] = token

    def remove(self, key):
        """Remove a token by key from the group."""
        if key in self._group_store:
            self._group_store.pop(key)

    def tokens(self) -> list:
        """Return a list of Tokens in the group."""
        return list(self._group_store.values())
