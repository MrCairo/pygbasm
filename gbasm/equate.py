"""
Manages EQU tokens
"""
import string
from gbasm.conversions import ExpressionConversion
from gbasm.label import Label
from gbasm.basic_lexer import BasicLexer, is_node_valid
from gbasm.constants import DIR, TOK, EQU, LBL, MULT

EC = ExpressionConversion

###############################################################################
class Equate:
    """
    Represents an EQU statement
    """
    _tok: dict = {}
    _label: Label = None

    def __init__(self, tokens: dict):
        self._tok = tokens

    def __str__(self):
        if self._label:
            desc = f"Label: {self._label.name()}\n"
            desc += f"Value: {hex(self._label.value())}\n"
            return desc
        return None

    def __repr__(self):
        desc = f"Equate({self._tok})"
        return desc

    @staticmethod
    def typename():
        """Returns the string name of this class's type."""
        return "Equate"

    @classmethod
    def from_string(cls, line: str):
        if line:
            tok = BasicLexer.from_text(line)
            if tok:
                tok.tokenize()
                return cls(tok.tokenized_list())
        return cls({})

    def parse(self):
        self._label = _EquateParser(self._tok).parse()

    def name(self):
        if self._label:
            return self._label.name()
        return None

    def value(self):
        if self._label:
            return self._label.value()
        return None

    # --------========[ End of class ]========-------- #

class _EquateParser:
    _tok: dict = {}
    def __init__(self, tokens: dict):
        """
        Parses the tokenized Equate statement. The dictionary consists of a
        an array with a label/EQU combination.
          [
            {'directive': 'LABEL', 'tokens': 'COUNT_LABEL'},
            {'directive': 'EQU', 'tokens': ['EQU', '$FFD2']}
          ]
        """
        self._tok = tokens

    def parse(self) -> dict:
        if self._tok is None:
            return None
        return self.validate()

    def validate(self) -> Label:
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
        val = EC().value_from_expression(equ_val)
        if val:
            return Label(label_name, val, force_const=True)
        return None

if __name__ == "__main__":
    e = Equate.from_string("COUNT_LABEL EQU $FFD2")
    e.parse()
    print(e)
