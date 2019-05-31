import pprint
from gbasm.conversions import ExpressionConversion
from gbasm.instruction.instruction_set import InstructionSet
from gbasm.exception import Error, ErrorCode
from gbasm.instruction import Registers
from gbasm.basic_lexer import BasicLexer, is_node_valid
from gbasm.constants import TOK
from gbasm.label import name_valid_label_chars, valid_label_first_char
EC = ExpressionConversion
IS = InstructionSet


class LexerTokens:
    """
    A data class that stores the instruction tokens and provides easy
    access to the token values.
    """

    _tok: dict

    def __init__(self, tokens: dict) -> None:
        self._tok = {} if "tok" not in tokens else tokens

    def tokens(self):
        """
        The raw tokens created by the lexer. It still may have values
        even if the instruction parsed was invalid.
        """
        return None if "tok" not in self._tok else self._tok["tok"]

    def opcode(self) -> str:
        """
        Returns the opcode (mnemonic) from the tokens
        """
        return self._exploded_val("opcode")

    def operands(self) -> [str]:
        """
        Returns the operands from the tokens
        """
        return self._exploded_val("operands")

    def definition(self) -> dict:
        """
        Returns the instruction definition as defined in the
        InstructionSet
        """
        ins_def = None if "ins_def" not in self._tok else self._tok["ins_def"]
        return ins_def

    def _exploded_val(self, key):
        tok = self.tokens()
        if not tok:
            return None
        ops = None if key not in tok else tok[key]
        return ops

    # --------========[ End of ParserTokens class ]========-------- #


class LexerResults:
    """
    Encapsulates a result from parsing an instruction. This class
    stores the bytearray of the parsed instruction or an error string.
    A Lexeresult object with out the 'data; property being set indicates
    a failed parse. In this case the '*error' properties should contain the
    error information (via the Error object). All methods return None if
    it's value doesn't exist either due to no data present.
    """
    _raw: dict = {}
    _tok: LexerTokens = {}

    def __init__(self, raw_results: dict, tokens: LexerTokens) -> None:
        self._raw = {} if raw_results is None else raw_results
        self._tok = {} if tokens is None else tokens

    def lexer_tokens(self) -> LexerTokens:
        """
        The tokenized values of the parsed instruction. The presense of tokens
        does NOT indicate a successful parse of the instruction.
        """
        return self._tok

    def addr(self) -> str:
        """
        Represents the opcode value of the instruction as hex string.
        Additional operand data does not appear here but instead
        appears in binary form via the binary() method or in text
        via the operand1() or operand2() methods.
        """
        return self._if_found("addr")

    def binary(self) -> bytes:
        """
        The binary representation of the parsed instruction.
        """
        return self._if_found("bytes")

    def cpu_cycles(self) -> list:
        """
        Informational only data that represents the number of CPU Cycles that
        the instruction takes.
        """
        return self._if_found("cycles")

    def flags(self) -> list:
        """
        An array of with the values of the Z, N, H, C CPU flags in that order.
        Z = Zero flag. A 'Z' indicates that the instruction can result in a
            zero value.
        N = Add/Sub flag. N = 1 if the previous operation was a subtract
        H = Half Cary flag. H = 1 if the add or subtract operation produced a
            carry into or borrow' from bit 4 of the accumulator.
        C = Carry/link flag C = 1 if the operltlon produced a carry from the
            MSB of the operand or result.
        - = Flag is unaffected by the operation.
        """
        f = ['-', '-', '-', '-']
        if "flags" in self._raw:
            for (idx, val) in enumerate(self._raw['flags'], start=0):
                if idx < 4:
                    f[idx] = val
        return f

    def length(self) -> int:
        """
        The length in bytes of the instruction. This is the opcode plus
        value-based operands if present.
        """
        return self._if_found("length")

    def mnemonic(self) -> str:
        """ The mnemonic (or opcode) of the instruction. """
        return self._if_found("mnemonic")

    def mnemonic_error(self) -> Error:
        """ The error if the mnemonic was invalid. """
        return self._if_found("mnemonic_error")

    def operand1(self) -> str:
        """ The first operand if present. """
        return self._if_found("operand1")

    def operand2(self) -> str:
        """ The second operand if present. """
        return self._if_found("operand2")

    def operand1_error(self) -> Error:
        """
        Contains the error found when processing operand1. A None
        indicates that there is no error.
        """
        return self._if_found("operand1_error")

    def clear_operand1_error(self) -> None:
        """
        Clears any operand1 error value. This is typically used if the
        operand was originally an error due to an unresolved label that
        gets resolved after this object was created.
        """
        if self._if_found("operand1_error"):
            del self._raw["operand1_error"]

    def operand2_error(self) -> Error:
        """
        Contains the error found when processing operand2. A None
        indicates that there is no error.
        """
        return self._if_found("operand2_error")

    def clear_operand2_error(self) -> None:
        """
        Clears any operand2 error value. This is typically used if the
        operand was originally an error due to an unresolved label that
        gets resolved after this object was created.
        """
        if self._if_found("operand2_error"):
            del self._raw["operand2_error"]

    def placeholder(self) -> str:
        """
        The placeholder found and processed in the instruction.
        A placeholder can be one of the following values:
        d8  = immediate 8 bit data.
        d16 = immediate 16 bit data.
        a8  = 8 bit unsigned data, which are added to $FF00 for certain
              instructions (replacement for missing IN and OUT instructions)
        a16 = a 16 bit address
        r8  = 8 bit signed data, which are added to program counter
        """
        return self._if_found("placeholder")

    def unresolved(self) -> str:
        """
        Returns any value that is/was considered unresolved when the
        instruction was initially parsed.
        """
        return self._if_found("unresolved")

    def is_valid(self):
        """
        Returns true if operand1 or operand2 contains an error.
        """
        test = self.mnemonic_error() is None and \
            self.operand1_error() is None and \
            self.operand2_error() is None
        return test

    def _if_found(self, key):
        return None if key not in self._raw else self._raw[key]

    # --------========[ End of LexerResults class ]========-------- #


class InstructionParser:
    """ Parses an individual instruction """
    _instruction_in = ""
    _tokens = None
    _final = {}
    state = None

    def __init__(self, node: dict):
        self.state = None
        if is_node_valid(node):
            self._final = self._parse(node[TOK])

    @classmethod
    def from_text(cls, instruction: str):
        """
        Constructs an InstructionParser object from an instruction string.
        """
        if instruction:
            lex = BasicLexer.from_text(instruction)
            if lex:
                lex.tokenize()
                return cls(lex.tokenized_list()[0])
        return cls({})

    def __repr__(self):
        pp = pprint.PrettyPrinter(indent=4)
        return pp.pformat(self._final)

    def result(self) -> LexerResults:
        """
        Returns the results from the lexer in a LexerResults object
        """
        return LexerResults(self._final, self._tokens)

    def raw_results(self) -> dict:
        """
        Returns the raw results from the lexer
        """
        return self._final

    def tokens(self) -> LexerTokens:
        """ Returns the tokenized parsed instruction """
        return self._tokens

    #                                             #
    # -----=====<  Private Functions  >=====----- #

    def _parse(self, tokens: dict) -> dict:
        """
        This parses the tokens created in the _tokenize function.
        """
        mnemonic = tokens[0]
        ins = IS().instruction_from_mnemonic(mnemonic)
        main = {"tok": {"opcode": mnemonic, "operands": tokens[1:]},
                "ins_def": ins}
        self._tokens = LexerTokens(main)
        tok = main["tok"]  # Tokenized instruction
        self.state = _State(main["ins_def"], {}, "")
        operands = [] if "operands" not in tok else tok["operands"]
        for (_, arg) in enumerate(operands, start=1):
            # True if the argument is within parens like "(HL)"
            self.state.arg = arg
            test = self._if_register()
            if test is True:
                continue
            elif test is not None:
                break
            if self.state.is_arg_in_roamer():  # A direct match (like NZ)
                self.state.roam_to_arg()
                self.state.set_operand_to_val(self.state.arg)
                continue
            else:  # Not a register or direct match. Maybe a number or label.
                if self._if_number():
                    continue
                # Is this _maybe_ a placeholder? Store it as a possible one.
                tmp = arg.strip("()")
                if tmp[0] in valid_label_first_char():
                    if name_valid_label_chars(tmp):
                        self.state.operands['unresolved'] = tmp
        if "!" in self.state.roamer:
            # This means that the instruction was found and processed
            dec_val = self.state.roamer["!"]
            byte = EC().expression_from_value(dec_val, "$")
            # Add the binary mnemonic value to the binary array (ba)
            hex_data = self._int_to_z80binary(dec_val)
            self.state.prepend_bytes(hex_data)
            return self.state.get_instruction_detail(byte)
        # Failiure case
        failure = {"mnemonic": mnemonic, "error": True}
        self.state.merge_operands(failure)
        failure = self.state.get_instruction_detail(None)
        return failure

    def _is_within_parens(self, value: str) -> bool:
        clean = value.strip()
        return clean.startswith("(") and clean.endswith(")")

    @staticmethod
    def plus_split(clean) -> list:
        _split = None
        if "(HL+)" in clean or "(HL-)" in clean:
            return None
        if "+" in clean:
            _tmp = clean.split("+")
            if len(_tmp) == 2:
                _split = _tmp
        return _split

    @staticmethod
    def _int_to_z80binary(dec_val, little_endian=True, bits=8) -> bytearray:
        """
        Converts the decimal value to binary format.
        Args:
        little_endian -- Default True, otherwise data is stored as hi, lo.
        bits -- The number of bits to include. Normally this is defined by the
                value. So, a value of $10 can be forced to be $0010 if bits=16.
                Or, a value of $ffd2 can be forced to $d2 if bits=8.
        """
        if dec_val < 0 or dec_val > 65535:
            return None
        ba = bytearray()
        hexi = f"%04x" % dec_val
        low = "0x" + hexi[2:]  # 0xffd2 == 0xd2
        high = "0x" + hexi[0:2]  # 0xffd2 == 0xff
        ba.append(int(low, 16))
        if bits == 16:
            ba.append(int(high, 16))
        # Normally little endian. If not, reverse the order to (hi, lo)
        if not little_endian and len(ba) == 2:
            ba.reverse()
        return ba

    def _if_register(self):
        """
        True if arg is a valid register for the instruction.
        False if arg is a valid register but not for this instruction.
        None if arg is not a valid register.
        """
        if Registers().is_valid_register(self.state.arg):
            if self.state.roam_to_arg():
                self.state.set_operand_to_val(self.state.arg)
                return True
            # A valid register, just not with this mnemonic
            arg = self.state.arg
            msg = f"Register {arg} is not valid with this mnemonic"
            err = Error(ErrorCode.INVALID_OPERAND,
                        supplimental=msg)
            self.state.set_operand_to_val(self.state.arg, err=err)
            return False
        return None

    def _if_number(self):
        _arg = self.state.arg
        arg_parens = False
        plus = None
        if self.state.is_arg_inside_parens():
            _arg = _arg.strip("()")
            arg_parens = True
        _split = InstructionParser.plus_split(_arg)
        if _split and len(_split) == 2:
            if _split[0] == "SP":
                plus = _arg
                _arg = _split[1]
        dec_val = EC().value_from_expression(_arg)
        if dec_val:  # Is this an immediate value?
            placeholder = self._ph_in_list(self.state.roamer.keys(),
                                           parens=arg_parens)
            if placeholder:
                bits = 8 if placeholder.find("8") != -1 else 16
                opbytes = self._int_to_z80binary(dec_val, bits=bits)
                self.state.append_bytes(opbytes)
                # If arg has parens then the placeholder must have
                # parens
                if arg_parens != self._is_within_parens(placeholder):
                    return False
                if self.state.is_arg_in_roamer(placeholder):
                    self.state.roam_to_arg()
                    self.state.operands["placeholder"] = placeholder
                    if plus:
                        self.state.operands[self.state.op_key] = plus
                    return True
        else:  # This is just info for an error. arg is NOT a number.
            msg = "The argument is not a numeric value"
            err = Error(ErrorCode.OPERAND_IS_NOT_NUMERIC,
                        supplimental=msg)
            self.state.set_operand_to_val(self.state.arg, err)
        return False

    def _ph_in_list(self, ph_list: list, bits="8", parens=False) -> str:
        """
        For all of the values in the instruction, if any are a placeholder
        then this function will validate and return the placeholder that
        apears in the list. Otherwise, None.
        """
        ph_key = None
        found = False
        regs = {"8": ["r8", "a8", "d8", "SP+r8"], "16": ["a16", "d16"]}
        eight = "8" if not parens else "8)"
        sixteen = "16" if not parens else "16)"
        if bits == "8":
            for k in ph_list:
                if k.find(eight) != -1:  # Maybe an 8-bit placeholder key
                    ph_key = k
                    break
        #if we are 16 bits or an 8-bit value isn't found...
        if not ph_key:
            for k in ph_list:
                if k.find(sixteen) != -1:
                    ph_key = k
                    break
        if ph_key:
            for r in regs["8"]:
                if ph_key.find(r) >= 0:
                    found = True
                    break
            if not found:
                for r in regs["16"]:
                    if ph_key.find(r) >= 0:
                        found = True
                        break
        if found:
            return ph_key
        return None

    # --------========[ End of InstructionParser class ]========-------- #


class _State:
    """ An internal lexer state class """
    roamer: dict
    operands: dict
    op_key: str
    err_key: str
    ins_bytes: bytearray
    _arg: str
    _op_idx: int

    def __init__(self, roamer, ops, arg) -> None:
        self.roamer = roamer
        self.operands = ops
        self._arg = arg
        self.op_key = "operand0"
        self._op_idx = 0
        self.inc_operand_index()
        self.ins_bytes = bytearray()

    def roam_to_arg(self, arg=None) -> bool:
        if arg is not None:
            self.arg = arg
        if self.arg in self.roamer:
            self.roamer = self.roamer[self.arg]
            self.operands[self.op_key] = self.arg
            return True
        return False

    def is_arg_in_roamer(self, arg=None):
        if arg is not None:
            self.arg = arg
        return self.arg in self.roamer

    def set_operand_to_val(self, val, err=None):
        self.operands[self.op_key] = val
        if err is not None:
            self.operands[self.err_key] = err
            self.roamer = {}
        self.inc_operand_index()

    def inc_operand_index(self):
        self._op_idx += 1
        self.op_key = "operand"+str(self._op_idx)
        self.err_key = self.op_key+"_error"

    def append_bytes(self, new_bytes: bytearray):
        if new_bytes:
            for b in new_bytes:
                self.ins_bytes.append(b)

    def prepend_bytes(self, new_bytes: bytearray):
        if new_bytes:
            for b in new_bytes:
                self.ins_bytes.insert(0, b)

    @property
    def arg(self):
        return self._arg

    @arg.setter
    def arg(self, value):
        clean = value.strip()
        self._arg = clean

    def is_arg_inside_parens(self, arg=None):
        if arg is not None:
            self.arg = arg
        return self._arg.startswith("(") and self._arg.endswith(")")

    def merge_operands(self, into: dict):
        if into:
            for key in self.operands.keys():
                into[key] = self.operands[key]

    def get_instruction_detail(self, byte: int) -> dict:
        if byte is None:
            final = {}
        else:
            final = InstructionSet().instruction_detail_from_byte(byte)
        if final is not None:
            final["bytes"] = bytes(self.ins_bytes)
            for item in ["placeholder", "operand1", "operand2",
                         "operand1_error", "operand2_error"]:
                if item in self.operands:
                    final[item] = self.operands[item]
        return final

    # --------========[ End of Insternal _State class ]========-------- #

if __name__ == "__main__":
    ip = InstructionParser.from_text("LD HL, SP+$45")
    print(ip)

    ip = InstructionParser.from_text("LD SP, $ffd2")
    print(ip)

    ip = InstructionParser.from_text("LD A, $45")
    print(ip)

    ip = InstructionParser.from_text("LD (GGG), SP")
    print(ip)

    ip = InstructionParser.from_text("ADD A, $10")
    print(ip)
