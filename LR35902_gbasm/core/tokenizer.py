"""Convert text to a tokenized dictionary."""

from __future__ import annotations
from typing import Optional
from collections import OrderedDict

from .conversions import ExpressionConversion
from .constants import DIRECTIVES, STORAGE_DIRECTIVES
from .constants import DIR, INST, STOR, BAD, SYM, ARGS, REMN
from .instruction_set import InstructionSet as IS
from .symbol import SymbolUtils

"""
The Tokenizer simply breaks up a line of text into a dictionary. The
dictionary starts off with a DIRECTIVE entry which identifies what the root
command of the input line is. If the directive contains other directives, an
additional DIRECTIVE entry is included.

  The text: "SECTION 'game_vars', WRAM0[$0100]" would generate tokens like:

  {'directive': 'SECTION',
   'arguments': {'arg00': 'SECTION',
                 'arg01': "'game_vars'",
                 'arg02': 'WRAM0[$0100]'}}

    - The 'directive' is the actual command, in this case a SECTION
      directive. The next part of the dictionary is an array of
      parameters. Parameter 0 is always the directive. The remaining
      parameters are there to support the directive.

  --------------------------------------------------

  {'directive': 'SYMBOL',
   'arguments': {'arg00': '.label:'},
   'remainder': {'directive': 'INSTRUCTION',
                 'arguments': {'arg00': 'LD',
                               'arg01': 'A',
                               'arg02': '(BC)'}}}

    - The presence of the 'tokens' key indicates that there are additional
      tokens that were processed as part of the input line. In the example
      above, the SYMBOL was on the same line as an INSTRUCTION.

"""

EC = ExpressionConversion


class TokenAssignment:
    """Various parsers for a set of tokens."""

    _tokens: list

    def __init__(self):
        """Initialize the object."""
        self._tokens = []

    def _id_tokens(self, tokens: dict):
        pass

    def parse_section(self, tokens):
        """Identify the tokens as SECTION."""
        pass

    def parse_instruction(self, tokens):
        """Identify the tokens as INS."""
        pass

    def parse_symbol(self, tokens):
        """Identify the tokens as SYM."""
        pass

    def parse_storage(self, tokens):
        """Identify the tokens as STOR."""
        pass


class Tokenizer:
    """Create tokens from a line of text."""

    def __init__(self):
        """Initialize a tokenizer instance."""

    @classmethod
    def tokenize(cls, line_of_text: str):
        """Convert line of text to tokens."""
        if len(line_of_text) == 0 or line_of_text is None:
            raise ValueError("Line of text must have a value")
        clean = Tokenizer._clean(line_of_text)

        pieces = clean.replace(',', ' ').split()
        token = Token()
        if pieces[0] in DIRECTIVES:
            token.directive = pieces[0]
            token.arguments = pieces
        elif pieces[0] in STORAGE_DIRECTIVES:
            token.directive = STOR
            token.arguments = pieces
        elif IS().is_mnemonic(pieces[0]):
            token.directive = INST
            token.arguments = pieces
        elif SymbolUtils.is_valid_symbol(pieces[0]):
            token.directive = SYM
            token.arguments = pieces

            # It is possible that more instructions are on the same line as
            # the symbol.
            if len(pieces) > 1:
                line2 = " ".join(pieces[1:])
                token.arguments = pieces[:1]
                token.remainder = Tokenizer.tokenize(line2)
        else:
            token.directive = BAD
            token.arguments = pieces

        return token

    @classmethod
    def _list_to_dict(cls, arr: list) -> dict:
        return {f"arg{idx:02d}": x for idx, x in enumerate(arr)}

    @classmethod
    def _clean(cls, text: str) -> str:
        cleaned = Tokenizer._join_parens(text.strip().split(";")[0])
        return cleaned

    @classmethod
    def _join_parens(cls, line) -> str:
        new_str = ""
        paren = 0
        for char in line:
            if char == " " and paren > 0:
                continue
            if char in "([{":
                paren += 1
            elif char in ")]}":
                paren -= 1
                paren = max(0, paren)  # If Negative set to 0
            new_str += char
        return new_str

    # --------========[ End of Tokenizer class ]========-------- #


class Token:
    """Accessor class for a Token dictionary."""

    def __init__(self):
        self._tok = OrderedDict()

    def __repr__(self):
        desc = f"Token.from_values(\"{self._tok[DIR]}\",\n"
        arr = "['" + "', '".join(self._tok[ARGS].values()) + "']"
        desc += f"{' ':18s}{arr}"
        if REMN in self._tok:
            desc += f",\n{' ':18s}{self._tok[REMN].__repr__()}"
        desc += ")"
        return desc

    def __str__(self):
        desc = f"DIRECTIVE = {self._tok[DIR]}\n"
        desc += f"ARGUMENTS = {self._tok[ARGS].values()}"
        return desc

    def raw(self) -> OrderedDict:
        """Return the backing dictionary."""
        tok = self._tok.copy()

        # Right now, only will have one optional REMN value.
        # There will not be nested REMN values inside of the
        # REMN object.
        if REMN in tok:
            remn: Token = tok[REMN]
            tok[REMN] = remn.raw()
        return tok

    @property
    def directive(self) -> Optional[str]:
        """Property getter to return the DIR value."""
        if DIR in self._tok:
            return self._tok[DIR]

        return None

    @directive.setter
    def directive(self, value: str):
        """Property setter to set the DIR value."""
        if value is not None:
            self._tok[DIR] = value

    @property
    def arguments(self) -> Optional[list]:
        """Return ARGS for this token."""
        if ARGS in self._tok:
            return self._tok[ARGS].values()

        return None

    @arguments.setter
    def arguments(self, value: list):
        """Set the ARGS for this token."""
        if value is not None:
            args = {f'arg{idx:02d}': x for idx, x in enumerate(value)}
            self._tok[ARGS] = args

    @property
    def remainder(self) -> Optional[Token]:
        """Get the REMN, if any, from this token."""
        if REMN in self._tok:
            return self._tok[REMN]

        return None

    @remainder.setter
    def remainder(self, value: Token):
        """Set the REMN value for this token."""
        if value is not None:
            self._tok[REMN] = value

    @classmethod
    def from_values(cls, directive: str, *, args: list,
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

    # --------========[ End of Token class ]========-------- #
