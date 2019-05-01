from gbasm.reader import Reader, BufferReader
from gbasm.conversions import ExpressionConversion

###############################################################################
class Equate (object):
    """
    """

    def __init__(self, line: str):
        self._line = line


    def parse(self) -> dict:
        line = self._line.upper()
        if "EQU" not in self._line:
            return None
        return self.__validate_line(line)


    def __validate_line(self, line) -> dict:
        """
        EQU line is always broken up as 'label EQU contant'.
        """
        parts = line.upper().split("EQU") # parts[0] == label, parts[1] == constant
        if len(parts) != 2:
            return None
        ec = ExpressionConversion()
        val = ec.value_from_expression(parts[1].strip())
        return {'type': 'EQU', 'label':parts[0].strip(), 'value':val }


if __name__ == "__main__":
    r = BufferReader("COUNT_LABEL EQU $FFD2")
    e = Equate("COUNT_LABEL EQU $FFD2")
    print(e.parse())
