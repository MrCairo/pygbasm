"""Classes that convert text into Tokens."""

from __future__ import annotations
from typing import Optional

from ..conversions import ExpressionConversion
from . import Token, TokenGroup

"""
The Tokenizer simply breaks up a line of text into a dictionary. The
dictionary starts off with a DIRECTIVE entry which identifies what the root
command of the input line is. If the directive contains other directives, an
additional DIRECTIVE entry is included.

------------------------------------------------------------------------------

It's important to note that tokenizing a line of text isn't the same thing as
validating the conents. While the actual basic items are identified -
Directive, instructions, or symbols - the parameters that appear after the
directive are not checked against syntax.

------------------------------------------------------------------------------

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


class Tokenizer:
    """Create tokens from a line of text."""

    def __init__(self):
        """Initialze the Tokenizer obect."""
        self._group = TokenGroup()

    def untokenize(self, token: Token) -> str:
        """Return the token as a single string."""
        desc = " ".join(token.arguments)
        if token.remainder is not None:
            tok2 = token.remainder.arguments
            desc += " ".join(tok2.arguments)

        return desc

    def tokenize(self, line_of_text: str) -> Optional(TokenGroup):
        """Convert line of text to tokens."""
        self._group = TokenGroup()
        self._generate(line_of_text)
        return self._group

    def _generate(self, line_of_text: str) -> bool:
        """Convert line of text to tokens."""
        if len(line_of_text) == 0 or line_of_text is None:
            return False

        clean = self.clean_text(line_of_text)
        if len(clean) == 0:
            return False

        # Break up into pieces and remove any empty elements
        pieces = [x for x in clean.split(" ") if x != ""]

        # Starting/ending Commas are irrelevant.
        pieces = [s.strip(",") for s in pieces]
        try:
            token = Token(pieces)
        except TypeError:
            return False
        self._group.add(token)

        # Add the token to the group. If there is remnant token data
        # go into that remnant token and add it to the group as well.
        # Continue to add remnant tokens until there are none. Generally,
        # there should only be at the most one remnant token but the
        # TokenGroup class is meant to handle as many as needed.
        rmn_token = token.remainder
        while rmn_token is not None:
            self._group.add(rmn_token)
            rmn_token = rmn_token.remainder
        return True

    def list_to_dict(self, arr: list) -> dict:
        """Convert a list to a dictionary with keys like argNN."""
        return {f"arg{idx:02d}": x for idx, x in enumerate(arr)}

    def clean_text(self, line_of_text: str) -> str:
        """Remove comments, leading/trailing spaces, and explode brackets."""
        cleaned = self._drop_comments(line_of_text)
        if len(cleaned) > 0:
            cleaned = self._explode_brackets(cleaned)
        return cleaned

    def _drop_comments(self, line_of_text) -> str:
        if line_of_text is not None:
            return line_of_text.strip().split(";")[0]
        return ""

    def _explode_brackets(self, text: str) -> str:
        """Return a string with brackets exploded for splitting."""
        """
        There are three types of brackets recognized:
            Round brackets: ()
            Square brackets: []
            Curly brackets: {}
        Also, the double quote and single quote values are also
        added to this as then also are used to enclose data.
        """
        brackets = "\"'([{}])"
        exploded = text
        if any(char in text for char in brackets):
            for char in brackets:
                exploded = exploded.replace(char, f" {char} ")
        return exploded

        # --------========[ End of Tokenizer class ]========-------- #
