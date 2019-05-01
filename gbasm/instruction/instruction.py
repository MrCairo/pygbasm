"""
These classes implements the Z80/LR35902 instruction set features
"""

from singleton_decorator import singleton
from gbasm.conversions import ExpressionConversion
from gbasm.instruction import Registers, InstructionSet
from gbasm.exception import Error, ErrorCode
from gbasm.constants import Constant
from gbasm.instruction.parser import InstructionParser
from typing import NewType

Address = NewType('Address', int)

###############################################################################


class Placeholder():
    """
    Encapsulates a placeholder which represents a replaceable mask with an
    actual value.  A placeholder is either a {8} or {16} which represents
    either an 8-bit or 16-bit value.
    """
    invalid = [None, Constant.UNDETERMINED, Constant.UNUSED]

    def __init__(self, placeholder: str, high: int, low: int):
        """If the placeholder is {8} then only the low_byte is set. If the
        placeholder is {16} then the high_byte and low_byte properties will
        be set. The high and low bytes should be passed in as a decemal
        value in the range of 0 - 255. If the value passed in is outside of
        this range, a ValueError exception will be thrown.  """

        if high and high not in range(0, 256) and high not in self.invalid:
            raise ValueError

        if low and low not in range(0, 256) and low != Constant.UNDETERMINED:
            raise ValueError

        if placeholder is None:
            raise ValueError

        self._placeholder = placeholder
        self._high_byte = high
        self._low_byte = low

    def __repr__(self):
        desc = f"Placeholder: {self.placeholder} "

        if self._high_byte not in self.invalid:
            hb = f"H:0x{self._high_byte:02x}"
        else:
            if self._high_byte == Constant.UNUSED:
                hb = "H:Not used "
            else:
                hb = "H:Undetermined"

        if self._low_byte not in self.invalid:
            lb = f"L:0x{self._low_byte:02x}"
        else:
            lb = "L:Undetermined"

        desc += f"{hb} {lb}\n"
        return desc


    @property
    def placeholder(self):
        return self._placeholder

    @property
    def high_byte(self):
        return self._high_byte

    @property
    def low_byte(self):
        return self._low_byte


###############################################################################
class ParseResults():
    """
    Encapsulates a result from parsing an instruction. This class
    stores the bytearray of the parsed instruction or an error string.
    A ParseResult object with out the 'data; property being set indicates
    a failed parse. In this case the 'error' property should contain the
    error information (via the Error object). A Parseresults object should
    never be instantiated with both the data and error value set to None.
    """
    def __init__(self, data: bytearray, error: Error = None,
                 placeholder: Placeholder = None):
        self._data = data
        self._error = error
        self._placeholder = placeholder

    @property
    def error(self) -> Error:
        "Return the error information (if available)"
        return self._error

    @property
    def data(self) -> bytearray:
        """Returns the resulting machine code (binary)."""
        return self._data

    @property
    def placeholder(self) -> Placeholder:
        """ If not none, the placeholder that was found during parsing."""
        return self._placeholder


###############################################################################


class Instruction():
    """ Encapsulates an individual Z80 instruction """

    def __init__(self, instruction: str):
        instruction = instruction.upper()
        clean = instruction.strip()
        self.instruction = clean.split(';')[0]
        self._parts = InstructionParser.explode(instruction)
        self._mnemonic = None if "opcode" not in self._parts \
            else self._parts["opcode"]
        self._operands = None if "operands" not in self._parts \
            else self._parts["operands"]
        ip = InstructionParser(instruction)
        self._parse_results = ip.result()
        self._placeholder_string = None

    def __repr__(self):
        desc = " Mnemonic = " + self._mnemonic + "\n"
        if self.operands:
            desc += "Arguments = " + ','.join(f"{x}" for x in self.operands)
            desc += "\n"

        if self._parse_results:
            if self._parse_results.data:
                desc += "code: "
                for byte in self._parse_results.data:
                    desc += f"{byte:02x} "
                desc += "\n"
            else:
                desc += self._parse_results.error.__repr__()
            if self._parse_results.placeholder:
                desc += " " + self._parse_results.placeholder.__repr__()
        return desc

    @property
    def mnemonic(self) -> str:
        """Represents the parsed mnemonic of the Instruction """
        return self._mnemonic

    @property
    def operands(self):
        """Returns an array of operands or None if there are no operands """
        return [] if self._operands is None else self._operands

    @property
    def machine_code(self) -> bytearray:
        """
        Returns the binary represent of the parsed instruction.
        This value will be None if the instruction was not parsed
        successfully.
        """
        return self._parse_results.data

    @property
    def placeholder_string(self) -> str:
        """
        Returns a custom string that is associated with a placeholder
        used by this object. This property simply allows the consumer
        of the object to associate an arbitrary string to the
        instruction for later retrieval. The property provides no
        other function and has no effect on the validity of the
        instruction object.
        """
        return self._placeholder_string

    @placeholder_string.setter
    def placeholder_string(self, value):
        """
        This property simply allows the consumer of the object to
        associate an arbitrary placeholder string with this
        object. The property provides no other function and has no
        effect on the validity of the instruction object.
        """
        self._placeholder_string = value

    @property
    def placeholder(self):
        if self._parse_results is not None:
            return self._parse_results.placeholder

    @property
    def parse_result(self):
        """The result of the parsing of the instruction. This value is
        established at object instantiation."""
        return self._parse_results

    def is_valid(self) -> bool:
        """
        Returns true if the Instruc object is valid. Validity is
        determined on whether the instruction was
        """
        return self._parse_results.data

    # class Instruction ends here
###############################################################################


###############################################################################
# Utility functions

# Aliases to class names I don't like to type (or fit within 79 chars)
###############################################################################


if __name__ == "__main__":
    ins = InstructionParser("JP NZ, $0010")
    print(ins)

    ins = InstructionParser("LD a, ($ff00)")
    print(ins)

    ins = InstructionParser("LD ($ff00), a")
    print(ins)

    ins = InstructionParser("RrCa")
    print(ins)

    ins = InstructionParser("Add HL, SP")
    print(ins)

    ins = InstructionParser("LD A, (HL-)")
    print(ins)

    ins = InstructionParser("ADD SP, $25")
    print(ins)

    ins = InstructionParser("LD b, c")
    print(ins)

    ins = InstructionParser("Nop")
    print(ins)

    ins = InstructionParser("JP (HL)")
    print(ins)

    ins = InstructionParser("LD A, ($aabb)")
    print(ins)

    ins = InstructionParser("SET 3, (HL)")
    print(ins)

    # Failures
    ins = InstructionParser("JR .RELATIVE")
    print(ins)

    ins = InstructionParser("NOP A")
    print(ins)
