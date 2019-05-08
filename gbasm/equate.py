"""
Manages EQU tokens
"""
import string
from gbasm.reader import BufferReader
from gbasm.conversions import ExpressionConversion
from gbasm.label import Label

###############################################################################
class Equate:
    """
    Represents an EQU statement
    """

    def __init__(self, line: str):
        self._line = line

    def parse(self) -> dict:
        if self._line is None:
            return None
        line = self._line.upper()
        if "EQU" not in self._line:
            return None
        rc = self._validate_line(line)
        if rc:
            return Label(rc["label"], rc["value"], force_const=True)
        return None

    def _validate_line(self, line: str) -> Label:
        """
        EQU line is always broken up as 'label EQU contant'.
        """
        parts = line.upper().split("EQU") # parts[0] == label, parts[1] == constant
        if len(parts) != 2:
            return None
        label_string: str = parts[0].strip()
        valid = string.ascii_letters + "_"
        for c in label_string:
            if c not in valid:
                label_string = None

        if label_string.isalpha() is False:
            return None
        EC = ExpressionConversion
        val = EC().value_from_expression(parts[1].strip())
        return {'label':parts[0].strip(), 'value':val}


if __name__ == "__main__":
    r = BufferReader("COUNT_LABEL EQU $FFD2", debug=True)
    e = Equate("COUNT_LABEL EQU $FFD2")
    print(e.parse())
