from singleton_decorator import singleton
from gbasm.instruction_set import InstructionSet
from gbasm.conversions import ExpressionConversion

###############################################################################
# Utility functions
@singleton
class InstructionHelper():
    """Helper functions for the Instruction* classes."""

    def explode(self, instruction: str) -> dict:
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

    def components_from_instruction(self, instruction):
        """
        Returns an array of values that represent the individual components
        of an instruction. For example 'LD B, (HL)' would result in an array
        like: ['LD', 'B', '(HL)']
        """
        components = []
        args = []

        if instruction is not None and instruction.strip():
            args = instruction.split(',')
            components = self.split_string(args[0].strip())
            if len(args) > 1:
                components += self.split_string(args[1])

        return components

    def encode_expression(self, expression):
        """
        This method converts an expression like:
            ($1000) or $1000 or $80 (or any numeric value)
        to actual binary values:
            0010 (little endian)
            80 (Just a single byte)
        If the expression is NOT a numeric value, this method
        will return a None instead of the following tuple:
            ('{16}', 0x10, 0x00) == (placeholder, high, low)
            or
            ('{8}', None, 0x80 } == (placeholder, no high, low)
            or
            ()
        The high/low indicate the high-byte (if present) and low byte.
        High byte is only present for 16-bit values.
        """
        item = expression

        if expression[0] == "(":
            item = expression.strip("(+-)")

        if Registers().is_valid_register(item):
            return None

        # if ($FFD2) change to ({16}) or $30 to {8}
        placeholder = ExpressionConversion().placeholder_from_expression(item)
        low = None
        high = None
        if placeholder is not None:
            # If the expression was with parens, replace
            # the expression and keep the parens.
            full_placeholder = expression.replace(item, placeholder)
            # Get the decimal value of the expression:
            #    $80 == 128, $1000 = 4096
            value = ExpressionConversion().value_from_expression(item)
            # Convert the value into a high/low hex value
            # so it can be included in the binary representation
            # of the final Instruction.
            if Constant.PLACEHOLDER_8 in placeholder:
                low = f"0x%02x" % value
            else:
                hexi = f"%04x" % value
                high = "0x" + hexi[0:2]  # 0xffd2 == 0xff
                low = "0x" + hexi[2:]  # 0xffd2 == 0xd2
        else:
            return None

        hi = Constant.UNUSED if high is None else int(high, 16)
        lo = None if low is None else int(low, 16)
        return Placeholder(full_placeholder, hi, lo)

    def placeholder_for_instruction(self, instruction: Instruction):
        """
        Parses the given Instruction object (i.e. LD A, $CA). The result
        is a ParseResults object with it's
        """
        mn = instruction.mnemonic
        operands = instruction.operands
        placeholder = None

        if InstructionSet().is_mnemonic(mn) is False:
            return None

        roamer = InstructionSet().instruction_from_mnemonic(mn)
        if "!" in roamer and not operands:
            return None

        index = 0

        for index in range(0, len(operands)):
            arg = str(operands[index])
            #
            # Convert the arg to a possible placeholder and a high/low byte
            # This means that $7F would be:
            # ph = {8}, high = None, low = 0x7f
            #
            # $1000 would be:
            # ph = {16}, high = 0x10, low = 0x00
            #
            # NOTE: For an instruction like "BIT 7, B", the '7' will not
            # erroneously be converted to an {8} since a decimal number must
            # start with a 0 and be more than 1 character in length.
            #
            ph, high, low = self.encode_expression(arg)
            if ph is not None:
                placeholder = ph
                break
                # whole instruction.

            if arg not in roamer:
                return None

            roamer = roamer[arg]
            index += 1

        return placeholder

    def parse_instruction(self, instruction: Instruction) -> ParseResults:
        """
        Parses the given Instruction object (i.e. LD A, $CA). The result
        is a ParseResults object with it's
        """
        mn = instruction.mnemonic
        operands = instruction.operands
        binary = bytearray()

        if InstructionSet().is_mnemonic(mn) is False:
            return ParseResults(None,
                                error=Error(ErrorCode.INVALID_MNEMONIC,
                                            supplimental=mn))

        roamer = InstructionSet().instruction_from_mnemonic(mn)

        #
        # This handles the mnemonic without op-code situation.
        # Like NOP
        #
        if "!" in roamer and not operands:
            binary.append(int(roamer["!"]))
            return ParseResults(binary)

        index = 0
        ph_high = ph_low = encode_result = None

        for index in range(0, len(operands)):
            arg = str(operands[index])
            #
            # Convert the arg to a possible placeholder and a high/low byte
            # This means that $7F would be:
            # ph = {8}, high = None, low = 0x7f
            #
            # $1000 would be:
            # ph = {16}, high = 0x10, low = 0x00
            #
            # NOTE: For an instruction like "BIT 7, B", the '7' will not
            # erroneously be converted to an {8} since a decimal number must
            # start with a 0 and be more than 1 character in length.
            #
            encode_result = self.encode_expression(arg)
            if encode_result is None:
                ph = high = low = None
            else:
                ph = encode_result.placeholder
                high = encode_result.high_byte
                low = encode_result.low_byte

                if high not in Placeholder.invalid:
                    high = hex(encode_result.high_byte)
                if low not in Placeholder.invalid:
                    low = hex(encode_result.low_byte)

            if ph is not None:
                # The placeholder values  are saved since they may be
                # overwritten in the next loop. We still need to write
                # the high (if present) and low values as part of the
                # whole instruction.
                arg = ph
                ph_high = high
                ph_low = low

            # This is an exception in the parsing algorithm. Basically, the RST
            # operations have an operand that must be devisibly by 8:
            # $00, $08, $10, $18, $20, $28, $30, $38 to be exact.
            # So instead of trying to generisize this and considering this is
            # the ONLY instruction that does this, we're performing this check
            # below.
            if mn == "RST" and ph == "{8}":
                val = int(ph_low, 16)
                arg = f"#${val:02x}"

            if arg not in roamer:
                # If the arg is not in the roamer it means a syntax
                # error or the arg is a label. Since a label generally
                # resolves to some numeric value, if a 8-bit or 16-bit
                # placeholder is found, we return it with the
                # ParseResults so that the caller can resolve and
                # properly process the label.
                ph = None
                for key in roamer.keys():
                    if Constant.PLACEHOLDER_8 in key:
                        ph = Placeholder(Constant.PLACEHOLDER_8,
                                         Constant.UNUSED,
                                         Constant.UNDETERMINED)
                        break
                if not ph:
                    for key in roamer.keys():
                        if Constant.PLACEHOLDER_16 in key:
                            ph = Placeholder(Constant.PLACEHOLDER_16,
                                             Constant.UNDETERMINED,
                                             Constant.UNDETERMINED)
                            break
                return ParseResults(None,
                                    error=Error(ErrorCode.INVALID_OPERAND,
                                                supplimental=arg),
                                    placeholder=ph)

            roamer = roamer[arg]
            val = None if "!" not in roamer else roamer["!"]
            if val:  # If not None, we found the instruction's hex op-code
                if val > 255:
                    # For high instruction binary, we keep it CB00
                    # and not a 00CB.
                    binary.append(int(val >> 8))
                    binary.append(int(val & 0x00ff))
                else:
                    binary.append(int(val))
                # For operand large binaries, it's little-endian
                # ($ffd2 becomes d2 ff)
                if ph_low not in Placeholder.invalid:
                    binary.append(int(ph_low, 16))
                if ph_high not in Placeholder.invalid:
                    binary.append(int(ph_high, 16))
                break
            index += 1

        #
        # Sanity check in the event the op_code dictionary is not correct.
        #
        if not binary:
            return ParseResults(None,
                                error=Error(ErrorCode.MISSING_MACHINE_CODE,
                                            supplimental=instruction.instruction))
        return ParseResults(binary, placeholder=encode_result)

    @staticmethod
    def split_string(string):
        """
        Splits the provided string using a space as a delimter.
        No empty elements are returned.
        """
        return list(filter(lambda x: len(x), string.split(' ')))
