"""
Manages EQU tokens
"""
import string
from .label import Label
from .conversions import ExpressionConversion
from .constants import TOK, DIR, LBL, EQU
from ..lexer.lexer_parser import BasicLexer

EC = ExpressionConversion
# TOK = const.TOK
# DIR = const.DIR
# LBL = const.LBL
# EQU = const.EQU

###############################################################################


class Equate:
    """Represent an EQU statement."""

    def __init__(self, tokens: dict):
        """Create an Equate object instance given an initial dictionary."""
        self._label: Label = None
        self._tok = tokens

    def __str__(self):
        """Return a string representatio n of this Equate object."""
        if self._label:
            desc = f"{self._label.name()} = {hex(self._label.value())}\n"
            return desc
        return None

    def __repr__(self):
        """Return a string respresendation of how the object was created."""
        desc = f"Equate({self._tok})"
        return desc

    @staticmethod
    def typename():
        """Return the string name of this class's type."""
        return EQU

    @classmethod
    def from_string(cls, line: str):
        """Create a new Equate object from a string."""
        if line:
            tok = BasicLexer.from_string(line)
            if tok:
                tok.tokenize()
                return cls(tok.tokenized_list())
        return cls({})

    def parse(self):
        """Parse the current Equate definition."""
        self._label = _EquateParser(self._tok).parse()

    def name(self):
        """Return the label name of the EQU."""
        if self._label:
            return self._label.name()
        return None

    def value(self):
        """Return the value of the EQU."""
        if self._label:
            return self._label.value()
        return None

    # --------========[ End of class ]========-------- #


class _EquateParser:
    """Euqate Statement Parser."""

    """
    Parses the tokenized Equate statement. The dictionary consists of a
        an array with a label/EQU combination.
          [
            {'directive': 'LABEL', 'tokens': 'COUNT_LABEL'},
            {'directive': 'EQU', 'tokens': ['EQU', '$FFD2']}
          ]
    """

    def __init__(self, tokens: dict):
        """Initialze the EQU Parser."""
        self._tok = tokens

    def parse(self) -> dict:
        if self._tok is None:
            return None
        return self.validate()

    def validate(self) -> Label:
        """Validate the EQU statement."""
        """
        An tokenized EQU consists of a LABEL and an EQU node.
        The EQU node will have a token that has two entries:
        A constant "EQU" and a value.

        [{'directive': 'LABEL', 'tokens': 'COUNT_LABEL'},
         {'directive': 'EQU', 'tokens': 'EQU', '$FFD2']}]
        """
        # Validate keys first.
        if self._tok[0][DIR] != LBL:
            return None
        if len(self._tok) < 2:
            return None
        label_name = self._tok[0][TOK]
        # keys are correct. Now capture/validate values.
        equ = self._tok[1][TOK]
        equ_val = equ[1]
        valid = string.ascii_letters + "_"
        for char in label_name:
            if char not in valid:
                return None
        val = EC().decimal_from_expression(equ_val)
        if val:
            return Label(label_name, val, constant=True)
        return None


if __name__ == "__main__":
    e = Equate.from_string("COUNT_LABEL EQU $FFD2")
    e.parse()
    print(e)
