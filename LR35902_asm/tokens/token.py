"""Hold a set of lexeme tokens."""

from __future__ import annotations
from typing import Optional
from collections import OrderedDict

from ..constants import DIR, ARGS, REMN, DIRECTIVES, INST, BAD, SYM
from ..instruction_set import InstructionSet as IS
from ..symbol import SymbolUtils

"""
A Token represents a set of lexemes that comprise a single line of source
code.

Example:

  The text: "SECTION 'game_vars', WRAM0[$0100]" would generate tokens like:

  {'directive': 'SECTION',
   'arguments': {'arg00': 'SECTION',
                 'arg01': "'game_vars'",
                 'arg02': 'WRAM0[$0100]'}}

  {'directive': 'SYMBOL',
   'arguments': {'arg00': '.label:'}}

    - The 'directive' is the actual command, in this case a SECTION
      directive. The next part of the dictionary is an array of
      parameters. Parameter 0 is always the directive. The remaining
      parameters are there to support the directive.

"""


class Token:
    """Object that encapsulates pieces of parsed data (lexemes).

    This object is an accessor class to the underlying data structure that
    represents a line of source code text. The Token class itself doesn't
    parse, but it is used to store the divided up pieces without resorting to
    an untyped dictionary.
    """

    def __init__(self, pieces: list):
        """Initialze the objet and backing store."""
        if pieces is None:
            raise ValueError("Missing list of lexemes as input.")
        self._tok = OrderedDict()
        self._assign(pieces)

    def __repr__(self) -> str:
        """Return representation on how this object can be built."""
        desc = f"Token.from_values(\"{self._tok[DIR]}\",\n"
        arr = "['" + "', '".join(self._tok[ARGS].values()) + "']"
        desc += f"{' ':18s}{arr}"
        if REMN in self._tok:
            desc += f",\n{' ':18s}{self._tok[REMN].__repr__()}"
        desc += ")\n"
        return desc

    def __str__(self) -> str:
        """Return a human readable string for this object."""
        desc = f"DIRECTIVE = {self._tok[DIR]}\n"
        desc += f"ARGUMENTS = {self._tok[ARGS].values()}"
        if REMN in self._tok:
            desc += f"REMAINDER = {self._tok[REMN].__str__()}"
        return desc

    @property
    def directive(self) -> Optional[str]:
        """Property getter to return the DIR value."""
        return self._tok[DIR] if DIR in self._tok else None

    @directive.setter
    def directive(self, value: str):
        """Property setter to set the DIR value."""
        self._tok[DIR] = value if value is not None else None

    @property
    def arguments(self) -> Optional[list]:
        """Return ARGS for this token."""
        return self._tok[ARGS].values() if ARGS in self._tok else None

    @arguments.setter
    def arguments(self, value: list):
        """Set the ARGS for this token."""
        if value is not None:
            args = {f'arg{idx:02d}': x for idx, x in enumerate(value)}
            self._tok[ARGS] = args

    @property
    def remainder(self) -> Optional[Token]:
        """Get the REMN, if any, from this token."""
        return self._tok[REMN] if REMN in self._tok else None

    @remainder.setter
    def remainder(self, value: Token):
        """Set the REMN value for this token."""
        if value is not None:
            self._tok[REMN] = value

    @classmethod
    def create_using(cls, directive: str, *, args: list,
                     remainder: Optional[Token] = None) -> Token:
        """Create a Token object from values."""
        tok = Token()
        if directive is not None:
            tok.directive = directive
        else:
            raise ValueError("'directive' must have a value")

        if args is not None:
            tok.arguments = args

        if remainder is not None:
            tok.remainder = remainder

        return tok

    def _assign(self, pieces: list):
        if pieces[0] in DIRECTIVES:
            self.directive = pieces[0]
            self.arguments = pieces
        elif IS().is_mnemonic(pieces[0]):
            self.directive = INST
            self.arguments = pieces
        elif SymbolUtils.is_valid_symbol(pieces[0]):
            self.directive = SYM
            self.arguments = pieces

            # It is possible that more instructions are on the same line as
            # the symbol.
            if len(pieces) > 1:
                self.arguments = pieces[:1]
                self.remainder = Token(pieces[1:])
        else:
            self.directive = BAD
            self.arguments = pieces

    # --------========[ End of Token class ]========-------- #
