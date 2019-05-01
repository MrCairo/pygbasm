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

class InstructionParser:
    """ Parses an individual instruction """
    def __init__(self, instruction: str):
        self._final = {}   # Final result dictionary.
        self.state = None
        if instruction:
            self._final = None
            tok = self._tokenize(instruction)
            if tok:
                self._final = self._parse(tok)

    def __repr__(self):
        pp = pprint.PrettyPrinter(indent=4)
        return pp.pformat(self._final)

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
        ops = {}
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
            final = InstructionSet().instruction_detail_from_byte(byte)
            if final:
                final["bytes"] = bytes(self.state.ins_bytes)
                for item in ["placeholder", "operand1", "operand2", "binary"]:
                    if item in :
                        final[item] = ops[item]
            self._final = final
            return final
        # Failiure case
        failure = {"mnemonic": mnemonic, "error": True}
        for item in ops:
            failure[item] = ops[item]
        return failure

    def result(self):
        return self._final

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
            self.roamer = None
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

    def get_instruction_detail(self, byte: int) -> dict:
        final = InstructionSet().instruction_detail_from_byte(byte)
        if final:
            final["bytes"] = bytes(self.state.ins_bytes)
            for item in ["placeholder", "operand1", "operand2", "binary"]:
                if item in self.operands:
                    final[item] = ops[item]



if __name__ == "__main__":
    ins = InstructionParser("JP NZ, $0010")
    print(ins)

    ins = InstructionParser("LD a, ($ff00)")
    print(ins)
