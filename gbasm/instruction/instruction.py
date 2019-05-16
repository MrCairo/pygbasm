"""
Class(es) that implements a Z80/LR35902 instruction and Instruction Set
"""
from gbasm.instruction.lexer_parser import LexerResults, InstructionParser
from gbasm.basic_lexer import BasicLexer, is_node_valid


class Instruction:
    """ Encapsulates an individual Z80 instruction """

    def __init__(self, tokens: dict):
        instruction = tokens
        instruction = instruction.upper()
        clean = instruction.strip()
        self.instruction = clean.split(';')[0]
        ip = InstructionParser(instruction)
        self._tokens = ip.tokens()
        self._lex_results: LexerResults = ip.result()
        self._placeholder_string = None


    @classmethod
    def from_text(cls, text: str):
        lex = BasicLexer.from_text(text)
        if lex:
            lex.tokenize()
            return cls(lex.tokenized_list())
        return cls({})

    def __repr__(self):
        desc = "   Mnemonic = " + self.mnemonic() + "\n"
        if self._lex_results.lexer_tokens().operands():
            desc +=  "  Arguments = " + ',' . \
                join(f"{x}" for x in
                     self._lex_results.lexer_tokens().operands())
            desc += "\n"
        if self._lex_results:
            if self.machine_code():
                desc += "       Code = "
                for byte in self.machine_code():
                    desc += f"{byte:02x} "
                desc += "\n"
            else:
                if self._lex_results.operand1_error():
                    desc += "  Op1 error = " + \
                        self._lex_results.operand1_error().__repr__()
                    desc += "\n"
                if self._lex_results.operand2_error():
                    desc += "  Op2 error = " + \
                        self._lex_results.operand2_error().__repr__()
                    desc += "\n"
            if self.placeholder():
                desc += "Placeholder = " + self.placeholder()
                desc += "\n"
        return desc

    def mnemonic(self) -> str:
        """Represents the parsed mnemonic of the Instruction """
        return self._lex_results.mnemonic()

    def operands(self):
        """Returns an array of operands or None if there are no operands """
        return [] if self._tokens.operands() is None else \
            self._tokens.operands()

    def machine_code(self) -> bytearray:
        """
        Returns the binary represent of the parsed instruction.
        This value will be None if the instruction was not parsed
        successfully.
        """
        return self._lex_results.binary()

    def placeholder(self) -> str:
        """
        Returns a custom string that is associated with a placeholder
        used by this object. This property simply allows the consumer
        of the object to associate an arbitrary string to the
        instruction for later retrieval. The property provides no
        other function and has no effect on the validity of the
        instruction object.
        """
        return self._lex_results.placeholder()

    def parse_result(self) -> LexerResults:
        """The result of the parsing of the instruction. This value is
        established at object instantiation."""
        return self._lex_results

    def is_valid(self) -> bool:
        """
        Returns true if the Instruc object is valid. Validity is
        determined on whether the instruction was parsed successfully.
        """
        return self._lex_results.mnemonic_error() is None

    # --------========[ End of Instruction class ]========-------- #


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
