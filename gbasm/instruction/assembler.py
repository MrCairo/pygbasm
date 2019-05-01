"""
These classes implements the Z80/LR35902 assembler
"""
from singleton_decorator import singleton
from gbasm.label import Labels, Label
from gbasm.constants import Constant
from gbasm.conversions import ExpressionConversion
from . import Instruction

"""
###############################################################################

Creates the Z80/LR35902 instruction set codes.
This class is implemented as a singleton.

"""
@singleton
class Assembler():
    """ Represents the entire Z80 instruction set """
    _all_registers = None
    mydata = None
    _jump_table = None


    def assemble_instruction(self, instruction:Instruction) -> bytes:
        """
        Assembles the instruction provided in 'inst_comp'.
        inst_comp are the all instruction values broken up as components each in
        an array element.
        """
        if self._jump_table is None:
            self._jump_table = {
                "ADD"  : _op_ADD,
                "AND"  : _op_AND,
                "BIT"  : _op_BIT,
                "CALL" : _op_CALL,
                "CCF"  : _op_CCF,
                "CP"   : _op_CP,
                "CPL"  : _op_CPL,
                "DAA"  : _op_DAA,
                "DEC"  : _op_DEC,
                "DI"   : _op_DI,
                "EI"   : _op_EI,
                "HALT" : _op_HALT,
                "INC"  : _op_INC,
                "JP"   : _op_JP,
                "JR"   : _op_JR,
                "LD"   : _op_LD,
                "LDH"  : _op_LDH,
                "NOP"  : _op_NOP,
                "OR"   : _op_OR,
                "POP"  : _op_POP,
                "PUSH" : _op_PUSH,
                "RES"  : _op_RES,
                "RET"  : _op_RET,
                "RETI" : _op_RETI,
                "RL"   : _op_RL,
                "RLA"  : _op_RLA,
                "RLC"  : _op_RLC,
                "RLCA" : _op_RLCA,
                "RR"   : _op_RR,
                "RRA"  : _op_RRA,
                "RRC"  : _op_RRC,
                "RRCA" : _op_RRCA,
                "RST"  : _op_RST,
                "SBC"  : _op_SBC,
                "SCF"  : _op_SCF,
                "SET"  : _op_SET,
                "SLA"  : _op_SLA,
                "SRA"  : _op_SRA,
                "SRL"  : _op_SRL,
                "STOP" : _op_STOP,
                "SUB"  : _op_SUB,
                "SWAP" : _op_SWAP,
                "XOR"  : _op_XOR
            }
        if instruction.mnemonic:
            base = instruction.operands[0]
            opcode_func = self._jump_table[base]
            if opcode_func:
                return opcode_func(instruction)
        else:
            return None


    def opcode_handler(self, inst_comp) -> bytes:
        if len(inst_comp) < 1: return None
        base = inst_comp[0]
        opcode_func = self.jump_table[base]
        if opcode_func is not None:
            return opcode_func(inst_comp)
        return None


    @staticmethod
    def twos_comp(val, bits):
        """compute the 2's complement of int value val"""
        if val & (1 << (bits - 1)) != 0:  # if sign bit is set e.g., 8bit: 128-255
            val = val - (1 << bits)        # compute negative value
        return val                         # return positive value as is

    # End of class Assembler
###############################################################################

"""
These functions handle each opcode. A jump table defined in the
opcode_handler function contains the table to jump to each function
based upon the starting mneumonic.
"""
def _op_ADD(args):
    pass

def _op_AND(args):
    pass

def _op_BIT(args):
    pass

def _op_CALL(args):
    pass

def _op_CCF(args):
    pass

def _op_CP(args):
    pass

def _op_CPL(args):
    pass

def _op_DAA(args):
    pass

def _op_DEC(args):
    pass

def _op_DI(args):
    pass

def _op_EI(args):
    pass

def _op_HALT(args):
    pass

def _op_INC(args):
    pass

def _op_JP(args):
    pass

def _op_JR(args):
    if len(args) == 2:
        num = ExpressionConversion().value_from_expression(args[1])
        if num is None:
            if Labels()[args[1]] is None:
                label = Label(args[1], Constant.PLACEHOLDER_OFFSET)
                Labels()[label.name] = label
                print(label)
                return [0x18, Constant.PLACEHOLDER_OFFSET]
            else:
                return [0x18, num]
            return [0x18, Constant.INVALID_VALUE]

def _op_LD(args) -> bytes:

    return [0x12]
pass

def _op_LDH(args):
    pass

def _op_NOP(args):
    pass

def _op_OR(args):
    pass

def _op_POP(args):
    pass

def _op_PUSH(args):
    pass

def _op_RES(args):
    pass

def _op_RET(args):
    pass

def _op_RETI(args):
    pass

def _op_RL(args):
    pass

def _op_RLA(args):
    pass

def _op_RLC(args):
    pass

def _op_RLCA(args):
    pass

def _op_RR(args):
    pass

def _op_RRA(args):
    pass

def _op_RRC(args):
    pass

def _op_RRCA(args):
    pass

def _op_RST(args):
    pass

def _op_SBC(args):
    pass

def _op_SCF(args):
    pass

def _op_SET(args):
    pass

def _op_SLA(args):
    pass

def _op_SRA(args):
    pass

def _op_SRL(args):
    pass

def _op_STOP(args):
    pass

def _op_SUB(args):
    pass

def _op_SWAP(args):
    pass

def _op_XOR(args):
    pass
