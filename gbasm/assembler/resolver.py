"""
This class (and accompanying functions) try to resolve labels assigned to
variable type values. Instructions that cannot be resolved are returned in
original state.
"""
import operator
from singleton_decorator import singleton

from ..core.lexer_results import LexerTokens, LexerResults
from ..core.conversions import ExpressionConversion as EC
from ..core.instruction_pointer import InstructionPointer as IP
from ..core.instruction import Instruction
from ..core.label import Label, Labels, LabelScope, LabelUtils

@singleton
class Resolver():
    """ Represents the entire Z80 instruction set """
    _jump_table = None

    def resolve_instruction(self,
                            instruction: Instruction,
                            current_address: int) -> Instruction:
        """
        Attempts top resolve instructions that failed initial resolution
        which can be due to the presence of a label. Only the instructions
        that can have variable parameters are processed. Any instruction
        that's is passed in that doesn't qualify for resolution is just
        returned.  current_address is used to compute relative offsets
        given a label with an absolute position.
        """
        if self._jump_table is None:
            self._jump_table = {
                "ADD"  : op_add,
                "CALL" : op_call,
                "JP"   : op_jp,
                "JR"   : op_jr,
                "LD"   : op_ld,
                "LDH"  : op_ldh,
            }
        if current_address < 0 or current_address > 65535:
            return instruction
        lex: LexerResults = instruction.parse_result()
        if lex and lex.mnemonic_error() is None:
            base = lex.mnemonic()
            if base not in self._jump_table:
                return instruction

            opcode_func = self._jump_table[base]
            if opcode_func:
                resolved = opcode_func(lex)
                return resolved if not None else instruction
        return instruction

    @staticmethod
    def twos_comp(val, bits):
        """compute the 2's complement of int value val"""
        if val & (1 << (bits - 1)) != 0:  # if sign bit is set e.g.(80-ff)
            val = val - (1 << bits)       # compute negative value
        return val                        # return positive value as is

    # --------========[ End of class ]========-------- #

###############################################################################

"""
These functions handle each opcode. A jump table defined in the
opcode_handler function contains the table to jump to each function
based upon the starting mneumonic.
"""
def maybe_label(text: str) -> Label:
    """
    Returns the Label object is the text string is the key to a Label
    object, otherwise None.
    """
    maybe = text.strip()
    label: Label = Labels()[maybe]
    return None if label is None else label

def format_with_parens(val: str, parens: bool):
    if parens:
        return f"({val})"
    return val

def op_add(lex: LexerResults) -> Instruction:
    """ Process ADD instructions """
    return None

def op_call(lex: LexerResults) -> Instruction:
    """ Process CALL instructions """
    return None

def op_jp(lex: LexerResults) -> Instruction:
    """ Process JP instructions """
    return None

def op_jr(lex: LexerResults) -> Instruction:
    """ Process the JR instruction """
    args = []
    clean_label = None
    # Must be at least one operand.
    if lex.operand1 is None:
        return None

    clean1 = lex.operand1().strip("()")
    paren1 = len(clean1) < len(lex.operand1())
    clean2 = None
    paren2 = False
    if lex.operand2():
        clean2 = lex.operand2().strip("()")
        paren2 = len(clean2) < len(lex.operand2())
    if lex.operand1_error():
        label = maybe_label(clean1)
        if label is None:
            return None
        clean_label = label
        print(f"RESOLVE JR compute relative IP = {hex(IP().location)}")
        print(f"from = {hex(label.value())}")
        rel = compute_relative(IP().location, label.value())
        print(f"Relative value is {rel}")
        rel = EC().expression_from_value(rel, "$")
        args.append(format_with_parens(rel, paren1))
        lex.clear_operand1_error()
    else:
        if lex.operand1() in ["NZ", "Z", "NC", "C"]:
            args.append(lex.operand1())
        else:
            val = EC().value_from_expression(clean1)
            if val:
                args.append(val)
            else:
                return None

    if lex.operand2_error():
        label = maybe_label(clean2)
        if label is None:
            return None
        clean_label = label
        rel = compute_relative(IP().location, label.value())
        #
        # JR NZ, 0x?? is two bytes in size. For negative values (0x80+)
        # reduce the relative by two bytes to account for going back
        # INCLUDING the instruction size. For anything less than 80,
        # we add two to include the instruction size. This will give a
        # range of -126 through +129.
        #
        if rel > 0x80:
            rel -= 2
        else:
            rel += 2

        val = EC().expression_from_value(rel, "$")
        args.append(format_with_parens(val, paren2))
        lex.clear_operand2_error()
    else:
        if lex.operand2():
            val = EC().value_from_expression(clean2)
            if val:
                args.append(format_with_parens(val, paren2))
                lex.clear_operand2_error()
            else:
                return None
    if len(args) == 2:
        ins = Instruction.from_string(f"JR {args[0]}, {args[1]}")
        ins.labels = [clean_label]
        return ins
    ins = Instruction.from_string(f"JR {args[0]}")
    ins.labels = [clean_label]
    return ins

def op_ld(lex: LexerResults) -> Instruction:
    args: list = []
    clean_labels = []
    if lex.operand1() is None or lex.operand2() is None:
        return None
    paren1 = paren2 = False
    clean1 = clean2 = None
    if lex.operand1_error():
        clean1 = lex.operand1().strip("()")
        paren1 = len(clean1) < len(lex.operand1())
        label = maybe_label(clean1)
        if label is None:
            if core.Registers().is_valid_register(clean1) is False:
                return None
        clean_labels.append(label)
        val = EC().expression_from_value(label.value(), "$")
        args.append(format_with_parens(val, paren1))
    else:
        args.append(lex.operand1())

    if lex.operand2_error():
        clean2 = lex.operand2().strip("()")
        paren2 = len(clean2) < len(lex.operand2())
        label = maybe_label(clean2)
        if label is None:
            # Not a label but is it a number?
            val = EC().value_from_expression(clean2)
            if val:
                args.append(format_with_parens(val, paren2))
            else:
                # If not a number, is this a valid register?
                # We test this here since if operand1 is in error, operand2
                # (if it exists) will also be in error.
                if core.Registers().is_valid_register(clean2) is False:
                    return None
                args.append(format_with_parens(clean2, paren2))
        else:
            val = EC().expression_from_value(label.value(), "$")
            args.append(format_with_parens(val, paren2))
            clean_labels.append(label)
    else:
        args.append(lex.operand2())

    text = f"LD {args[0]}, {args[1]}"
    ins = Instruction.from_string(text)
    ins.labels = clean_labels
    return ins


def op_ldh(lex: LexerResults) -> Instruction:
    return None

def compute_relative(curr, base) -> int:
    """
    Compute a relative 8-bit value
    """
    if curr > base:
        rel = base - curr
    else:
        rel = curr - base

    if rel < -128 or rel > 127:
        return None

    if rel < 0:
        return twos_comp(rel)
    else:
        return rel

def twos_comp(val, bits=8) -> int:
    """compute the 2's complement of int value val"""
    if val < 0:
        ones = ones_comp(val, bits)
        return abs(ones) + 1
    return val

def ones_comp(val, bits=8) -> int:
    if val < 0:
        mask = (2**bits) - 1
        return operator.xor(abs(val), mask)
    return val
