"""
These clases are used to parse an individual Z80 instruction
"""
import pprint
from gbasm.conversions import ExpressionConversion
from gbasm.instruction import InstructionSet
from gbasm.instruction import Registers
from gbasm.exception import Error, ErrorCode

EC = ExpressionConversion
IS = InstructionSet


class ParserTokens:
    """
    A data class that stores the instruction tokens and provides easy
    access to the token values.
    """

    _tok: dict

    def __init__(self, tokens: dict) -> None:
        self._tok = {} if "tok" not in tokens else tokens

    def tokens(self):
        """
        The raw tokens created by the parser. It still may have values
        even if the instruction parsed was invalid.
        """
        return None if "tok" not in self._tok else self._tok["tok"]

    def opcode(self) -> str:
        """
        Returns the opcode (mnemonic) from the tokens
        """
        return self._exploded_val("opcode")

    def operands(self) -> str:
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

###############################################################################

"""
{   'addr': '$c4',
    'bytes': b'\xc4\x12\x00',
    'cycles': [24, 12],
    'flags': ['-', '-', '-', '-'],
    'length': 3,
    'mnemonic': 'CALL',
    'operand1': 'NZ',
    'operand2': 'a16',
    'placeholder': 'a16'}
"""


class ParserResults():
    """
    Encapsulates a result from parsing an instruction. This class
    stores the bytearray of the parsed instruction or an error string.
    A ParseResult object with out the 'data; property being set indicates
    a failed parse. In this case the 'error' property should contain the
    error information (via the Error object). A Parseresults object should
    never be instantiated with both the data and error value set to None.
    """
    _raw: dict = {}

    def __init__(self, raw_results: dict) -> None:
        self._raw = {} if raw_results is None else raw_results

    def addr(self) -> str:
        return self._if_found("addr")

    def binary(self) -> bytes:
        return self._if_found("bytes")

    def cpu_cycles(self) -> list:
        return self._if_found("cycles")

    def flags(self) -> list:
        f = ['-', '-', '-', '-']
        if "flags" in self._raw:
            for (idx, val) in enumerate(self._raw['flags'], start=0):
                if idx < 4:
                    f[idx] = val
        return f

    def length(self) -> int:
        return self._if_found("length")

    def mnemonic(self) -> str:
        return self._if_found("mnemonic")

    def operand1(self) -> str:
        return self._if_found("operand1")

    def operand2(self) -> str:
        return self._if_found("operand2")

    def operand1_error(self) -> Error:
        return self._if_found("operand1_error")

    def operand2_error(self) -> Error:
        return self._if_found("operand2_error")

    def placeholder(self) -> str:
        return self._if_found("placeholder")

    def _if_found(self, key):
        return None if key not in self._raw else self._raw[key]

###############################################################################


class InstructionParser:
    """ Parses an individual instruction """
    def __init__(self, instruction: str):
        self._final = {}   # Final result dictionary.
        self.state = None
        self._tokens = None
        if instruction:
            self._final = None
            tok = self._tokenize(instruction)
            if tok:
                self._final = self._parse(tok)

    def __repr__(self):
        pp = pprint.PrettyPrinter(indent=4)
        return pp.pformat(self._final)

    def result(self) -> ParserResults:
        """
        Returns the results from the parser in a ParserResults object
        """
        return ParserResults(self._final)

    def raw_results(self) -> dict:
        """
        Returns the raw results from the parser
        """
        return self._final

    def tokens(self) -> ParserTokens:
        """ Returns the tokenized parsed instruction """
        return self._tokens

    @staticmethod
    def _explode(instruction: str) -> dict:
        """
        Returns an array of values that represent the individual
        components of an instruction. For example 'LD B, (HL)' would
        result in an array like: ['LD', 'B', '(HL)']
        """
        def clean_split(str_in) -> [str]:
            return list(filter(lambda x: len(x), str_in.split(' ')))
        components = []
        args = []
        if instruction and instruction.strip():
            args = instruction.upper().split(',')
            components = clean_split(args.pop(0).strip())
            opcode = components.pop(0)
            components += [x for x in args]
        if not components:
            return {"opcode": opcode}
        return {"opcode": opcode, "operands": components}

    def _tokenize(self, instruction) -> dict:
        """
        Tokenizes the instruction into a mnemonic (opcode) and
        operands.
        """
        clean = instruction.upper().split(";")[0]  # ignore comments
        if not clean:
            return None
        exploded = self._explode(clean)
        result = None
        if exploded:
            if "opcode" in exploded:
                ins = IS().instruction_from_mnemonic(exploded["opcode"])
                result = {"tok": exploded,
                          "ins_def": ins}
        self._tokens = ParserTokens(result)
        return result

    def _parse(self, tokens: dict) -> dict:
        """
        This parses the tokens created in the _tokenize function.
        """
        if "tok" not in tokens or "ins_def" not in tokens:
            return None
        tok = tokens["tok"]       # Tokenized instruction
        self.state = _State(tokens["ins_def"], {}, "")
        mnemonic = tok["opcode"]
        operands = [] if "operands" not in tok else tok["operands"]
        for (idx, arg) in enumerate(operands, start=1):
            # True if the argument is within parens like "(HL)"
            self.state.arg = arg
            test = self._if_register()
            if test is True:
                continue
            if test is False:
                break
            if self.state.is_arg_in_roamer():  # A direct match (like NZ)
                self.state.roam_to_arg()
                self.state.set_operand_to_val(self.state.arg)
                continue
            else:  # Not a register or direct match. Maybe a number or label.
                if self._if_number():
                    continue
                break
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
        if failure:
            failure["mnemonic"] = mnemonic
        return failure

    def _is_within_parens(self, value: str) -> bool:
        clean = value.strip()
        return (clean.startswith("(") and clean.endswith(")"))

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
            else:
                # A valid register, just not with this mnemonic
                arg = self.state.arg
                msg = f"Register {arg} is not valid with this mnemonic"
                err = Error(ErrorCode.INVALID_OPERAND,
                            supplimental=msg)
                self.state.set_operand_to_val(self.state.arg, err=err)
                return False
        return None

    def _if_number(self):
        arg = self.state.arg
        arg_parens = False
        if self.state.is_arg_inside_parens():
            arg = arg.strip("()")
            arg_parens = True
        dec_val = ExpressionConversion().value_from_expression(arg)
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
        regs = {"8": ["r8", "a8", "d8"], "16": ["a16", "d16"]}
        eight = "8" if not parens else "8)"
        sixteen = "16" if not parens else "16)"
        for k in ph_list:
            if k.find(eight) != -1:  # Maybe an 8-bit placeholder key
                ph_key = k
                break
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


class _State:
    """ An internal parser state class """
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
        return (self.arg in self.roamer)

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
        return (self._arg.startswith("(") and self._arg.endswith(")"))

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

#    def make_results(self):


###############################################################################

if __name__ == "__main__":
    ins = InstructionParser("JP NZ, xxxx")
    print(ins)

    ins = InstructionParser("LD a, ($ff00)")
    print(ins)

    ins = InstructionParser("DEC D")
    print(ins)

    ins = InstructionParser("CALL NZ $12")
    print(ins)
