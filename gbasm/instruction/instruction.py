"""
These classes implements the Z80/LR35902 instruction set features
"""

from gbasm.constants import Constant
from gbasm.instruction.parser import InstructionParser
from gbasm.exception import Error, ErrorCode
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


class Instruction():
    """ Encapsulates an individual Z80 instruction """

    def __init__(self, instruction: str):
        instruction = instruction.upper()
        clean = instruction.strip()
        self.instruction = clean.split(';')[0]
        ip = InstructionParser(instruction)
        self._tokens = ip.tokens()
        self._parse_results = ip.result()
        self._placeholder_string = None

    def __repr__(self):
        desc = "   Mnemonic = " + self._tokens.opcode() + "\n"
        if self.operands:
            desc +=  "  Arguments = " + ',' . \
                join(f"{x}" for x in self._tokens.operands())
            desc += "\n"

        if self._parse_results:
            if self._parse_results.binary():
                desc += "       Code = "
                for byte in self._parse_results.binary():
                    desc += f"{byte:02x} "
                desc += "\n"
            else:
                if self._parse_results.operand1_error():
                    desc += "  Op1 error = " + \
                        self._parse_results.operand1_error().__repr__()
                    desc += "\n"
                if self._parse_results.operand2_error():
                    desc += "  Op2 error = " + \
                        self._parse_results.operand2_error().__repr__()
                    desc += "\n"
            if self._parse_results.placeholder():
                desc += "Placeholder = " + self._parse_results.placeholder()
                desc += "\n"
        return desc

    @property
    def mnemonic(self) -> str:
        """Represents the parsed mnemonic of the Instruction """
        return self._tokens.opcode()

    @property
    def operands(self):
        """Returns an array of operands or None if there are no operands """
        return [] if self._tokens.operands() is None else \
            self._tokens.operands()

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
        return self._parse_results.bytes is not None

    # class Instruction ends here


###############################################################################


if __name__ == "__main__":
    ins = Instruction("JP NZ, $0010")
    print(ins)

    ins = Instruction("LD a, ($ff00)")
    print(ins)

    ins = Instruction("LD ($ff00), a")
    print(ins)

    ins = Instruction("RrCa")
    print(ins)

    ins = Instruction("Add HL, SP")
    print(ins)

    ins = Instruction("LD A, (HL-)")
    print(ins)

    ins = Instruction("ADD SP, $25")
    print(ins)

    ins = Instruction("LD b, c")
    print(ins)

    ins = Instruction("Nop")
    print(ins)

    ins = Instruction("JP (HL)")
    print(ins)

    ins = Instruction("LD A, ($aabb)")
    print(ins)

    ins = Instruction("SET 3, (HL)")
    print(ins)

    # Failures
    ins = Instruction("JR .RELATIVE")
    print(ins)

    ins = Instruction("NOP A")
    print(ins)
