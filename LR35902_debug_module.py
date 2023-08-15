"""Quickly test various fetaures before going to unit tests."""


from LR35902_gbasm.core import Section, InstructionPointer, \
    ExpressionConversion, Label, Expression
from LR35902_gbasm.core.tokens import Tokenizer, Token


class DebugFunctions:
    """Class for debugging. Not a unit test file."""

    def __init__(self):
        """Create the DebugFunctions class."""
        self._ip = InstructionPointer()
        self._ec = ExpressionConversion()

    def section_with_offset(self):
        """Debugs a basic SECTION."""
        line = 'SECTION "game_vars", WRAM0[$C100]'
        section = Section.from_string(line)
        print(section)

    def basic_label(self):
        """Execute variouls label functions."""
        self._ip.base_address = 0xC100
        my_label = Label("Mitch", 0xC100)
        print(my_label)

    def convert_things(self):
        """Convert expressions."""
        expr = Expression('$beef')
        print(expr.prefix)
        print(expr.raw_value)
        print(expr.descriptor.value_base)
        print(expr.type)
        print(expr.to_decimal())


if __name__ == "__main__":
    dbg = DebugFunctions()

    tkn2 = Token.create_using("STORAGE",
                              args=['DB', '$00', '$01', '$01', '$02', '$03',
                                    '$FE', '$18', '$0d', '021', '%00100010'],
                              remainder=None)

    tkn = Token.create_using("SYMBOL",
                             args=['.label:'], remainder=tkn2)

    print(tkn.__repr__())

    line = "SECTION 'game_vars', WRAM0[$0100], bank 1"
    token_group = Tokenizer().tokenize(line)
    print(token_group)

    line = ".label: DB $FF,$00,$FF,$00,$FF,$00,$FF,$00,$FF,$00,$FF,$00,$FF"
    token_group = Tokenizer().tokenize(line)
    print(token_group)

    # *Python :: Run file from project directory
