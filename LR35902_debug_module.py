
""" Section Debug Testing. """
import pprint
from LR35902_gbasm.core import Section, InstructionPointer,\
    ExpressionConversion, Label, Expression, tokenize_line


class DebugFunctions:
    """Class for debugging. Not a unit test file"""

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

        tok = tokenize_line('SECTION "game_vars", WRAM0[$0100]')
        pprint.pprint(tok)
#        value = self._ec.decimal_from_expression("$FFD2")
#        pprint.pprint(value)
#        value = self._ec.expression_from_decimal(1000, "$")
#        value = self._ec.expression_type_from_expression("'Label'")
#        pprint.pprint(value)


if __name__ == "__main__":
    dbg = DebugFunctions()
    dbg.convert_things()
