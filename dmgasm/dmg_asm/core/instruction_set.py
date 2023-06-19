"""
Class(es) that implements a Z80/LR35902 instruction and Instruction Set
"""
import os, io, json
from decimal import Decimal
from singleton_decorator import singleton

from .lr35902_data import LR35902Data
from .registers import Registers
from .conversions import ExpressionConversion

#
# Special internal functions.
#
def _gen_LR35902_inst() -> dict:
    #-------------------------------------------------------
    def _load_cpu_data() -> dict:
        try:
            return json.load(io.StringIO(LR35902Data().json))
        except json.JSONDecodeError:
            return None
    #-------------------------------------------------------

    EC = ExpressionConversion()
    raw_data = _load_cpu_data()

    if raw_data is None:
        return None

    instructions = {}

    """
    This creates a 'shorthand' version of the LR35902 instruction set that
    makes it easier to look up and parse.
    """
    for hex_code in raw_data:
        node = raw_data[hex_code]
        mnemonic = node['mnemonic'] if 'mnemonic' in node else None
        if mnemonic is None or mnemonic == "PREFIX":
            continue

        term = {"!": EC.value_from_expression(hex_code)}
        op1 = node["operand1"] if "operand1" in node else None
        op2 = node["operand2"] if "operand2" in node else None

        existing = {} if mnemonic not in instructions \
            else instructions[mnemonic]

        line = term
        if op1 is not None:
            # Compute what the final line will be:
            #   Only op1:
            #       "JR": {"r8": {"!": 0x18}
            #   Op1 and Op2:
            #       "LD":  {"BC": {"d16": {"!": 0x01}}
            line = {op1:term} if op2 is None else {op1:{op2: term}}
            if op1 not in existing:
                existing[op1] = line[op1]
            else:
                existing[op1].update(line[op1])
        else:
            # Handles mnemonics without op codes:
            #   "NOP": {"!": 0x00}
            existing = line
        instructions[mnemonic] = existing
    # End for
    return {"instructions":instructions, "raw_data":raw_data}
###############################################################################


@singleton
class InstructionSet(object):
    """This represents the LR35902 CPU instruction set and is implemented
    as a singleton object. The instruction set returned is done in a type
    of 'shorthand' that makes parsing and traversing easy.

    Examples:
        'ADD': { 'A': { '(HL)': { '!': 0x86 }}}
        'LD': { '(a16)': { 'A': { '!': 0xea }}}
        'CPL': { '!': 0x2f }

    Addresses and register placeholders in the instruction set are defined
    as follows:

      d8:  Immediate 8-bit data.

      d16: Immediate 16-bit data.

      a8:  8 bit unsigned data, which are added to $FF00 in certain
           instructions (replacement for missing IN and OUT instructions).

      a16: 16-bit address

      r8:  8-bit signed data which are added to the program counter.

    For an instruction key value is "!":
      !    Represents the end of instruction data mostly made for the internal
           mnemonic roamer. If lets the roamer know when it has reached the end
           of a specific mnemonic within the dictionary list.

    """
    data = _gen_LR35902_inst()
    LR35902 = data["instructions"]
    LR35902_detail = data["raw_data"]

    def __init__(self):
        pass
        # -----=====< End of __init__() >=====----- #

    def instruction_from_mnemonic(self, mnemonic: str) -> dict:
        """Returns the instruction definition dict for the given
        mnemonic"""
        return self.LR35902[mnemonic] if mnemonic in self.LR35902 else None

    def instruction_detail_from_byte(self, byte: str) -> dict:
        return self.LR35902_detail[byte] \
            if byte in self.LR35902_detail else None

    @property
    def instruction_set(self):
        """ Returns the Z80 instruction set as a dictionary. """
        return self.LR35902

    def is_mnemonic(self, mnemonic_string: str) -> bool:
        return True if mnemonic_string.upper() in self.LR35902 else False

    #                                             #
    # -----=====<  Private Functions  >=====----- #

    def _merge(self, target, source):
        return source if target is None else {**target, **source}

# --------========[ End of InstructionSet class ]========-------- #


if __name__ == "__main__":
    import pprint
    pp = pprint.PrettyPrinter(indent=4, compact=False, width=40)
    pp.pprint(InstructionSet().LR35902)
