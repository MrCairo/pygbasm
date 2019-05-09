"""
This class (and accompanying functions) try to resolve labels assigned to
variable type values. Instructions that cannot be resolved are returned in
original state.
"""
from singleton_decorator import singleton
from gbasm.label import Labels, Label
from gbasm.conversions import ExpressionConversion
from gbasm.instruction import LexerResults, Instruction

EC = ExpressionConversion

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
        that's that is passed in that doesn't qualify for resolution is
        just returned.
        current_address is used to compute relative offsets given a label
        with an absolute position.
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

# def resolve_label(label: str, lexer_result: LexerResults,
#                   base_address: int):
#     if base_address < 0 or base_address > 65535:
#         return None

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
        return(f"({val})")
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
        args.append(format_with_parens(label.value, paren1))
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
        args.append(format_with_parens(label.value, paren2))
    else:
        if lex.operand2():
            val = EC().value_from_expression(clean2)
            if val:
                args.append(format_with_parens(val, paren2))
            else:
                return None
    if len(args) == 2:
        return Instruction(f"JR {args[0]}, {args[1]}")
    else:
        return Instruction(f"JR {args[0]}")

def op_ld(lex: LexerResults) -> Instruction:
    args: list = []
    if lex.operand1() is None or lex.operand2() is None:
        return None
    paren1 = paren2 = False
    clean1 = clean2 = None
    if lex.operand1_error():
        clean1 = lex.operand1().strip("()")
        paren1 = len(clean1) < len(lex.operand1())
        label = maybe_label(lex.operand1)
        if label is None:
            return None
        args.append(format_with_parens(label.val, paren1))
    else:
        args.append(lex.operand1())

    if lex.operand2_error():
        clean2 = lex.operand2().strip("()")
        paren2 = len(clean2) < len(lex.operand2())
        label = maybe_label(clean2)
        if label is None:
            val = EC().value_from_expression(clean2)
            if val:
                args.append(format_with_parens(val, paren2))
            else:
                return None
        else:
            val = EC().expression_from_value(label.value(), "$")
            args.append(format_with_parens(val, paren2))
    else:
        args.append(lex.operand2())

    text = f"LD {args[0]}, {args[1]}"
    return Instruction(text)

def op_ldh(lex: LexerResults) -> Instruction:
    return None
