"""
Quickly test various fetaures before going to unit tests.
"""

from abc import ABC, abstractmethod
import string
import sys
from collections import namedtuple

from LR35902_gbasm.core import Section, InstructionPointer
from LR35902_gbasm.core import ExpressionConversion, Label, Expression
from LR35902_gbasm.core.tokens import Tokenizer

MinMax = namedtuple("MinMax", ['min', 'max'])


class Validator(ABC):
    """Abstract class to validate something."""

    def __set_name__(self, owner, name):
        """Set a named attribute of a generic object."""
        self.private_name = '_' + name

    def __get__(self, obj, objtype=None):
        """Get the value of a named attribute."""
        return getattr(obj, self.private_name)

    def __set__(self, obj, value):
        """Set the value of a named attribute."""
        self.validate(value)
        setattr(obj, self.private_name, value)

    @abstractmethod
    def validate(self, value):
        """Override this in any subclass ti validate the value."""
        pass


class OneOf(Validator):
    """Verifie that a value is one of a restricted set of options."""

    def __init__(self, *options):
        """Initialize the OneOf Object."""
        self.options = set(options)

    def validate(self, value):
        """Validate the OneOf object with against specific value."""
        if value not in self.options:
            raise ValueError(
                f'Expected {value!r} to be one of {self.options!r}'
            )


class BaseValue(Validator):
    """A class that represents a value with n digits of min/max values."""

    def __init__(self, digits: MinMax = None, range: MinMax = None, base=10):
        """Initialie the object with # of digits and min/max values."""
        """
        digits represent the min and max nummber of digits.
        range represents the base-10 min/max values of this object.
        """
        self.digits = digits
        self.range = range
        self.base = base
        if base not in [2, 8, 10, 16]:
            raise TypeError(f'Base can only 2, 8, 10 or 16 but was {base}')

    def validate(self, value):
        """Validate this object against a specific value."""
        if not isinstance(value, str):
            raise TypeError(f'Expected {value!r} to be a str.')

        # -- digits validation --
        if self.digits is None:
            raise AttributeError('Expected digits to be defined but got None')
        if len(value) < self.digits.min:
            raise ValueError(
                f'{value} must have at least {self.digits.min} digits.'
            )
        if len(value) > self.digits.max:
            raise ValueError(f'{value} exceeds {self.digits.max} digits.')

        # -- range validation value transformed to base-10 --
        if self.range is None:
            raise AttributeError('Expected range to be defined but got None')
        dec_val = int(value, self.base)
        if dec_val < self.range.min:
            raise ValueError(
                f'Expected {value!r} to be at least {self.range.min!r}'
            )
        if dec_val > self.range.max:
            raise ValueError(
                f'Expected {value!r} to be no more than {self.range.min!r}'
            )


class HexValue:
    """Represent a Hexidecimal value either 2 or 4 digits."""

    hex_value = BaseValue(digits=MinMax(2, 4),
                          range=MinMax(0, 65535),
                          base=16)

    def __init__(self, value: str):
        """Initialize the HexValue object."""
        if all(c in string.hexdigits for c in value) is False:
            raise TypeError(
                f'Value {value!r} must contain only hexidecimal digits.'
            )
        self.hex_value = value


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
        expr = Expression('0x1000')
        print(expr)


if __name__ == "__main__":
    dbg = DebugFunctions()

    h = HexValue("ABCD")
    sys.exit(0)

    dbg.convert_things()
    # tkn2 = Token.create_using("STORAGE",
    #                        args=['DB', '$00', '$01', '$01', '$02', '$03',
    #                              '$FE', '$18', '$0d', '021', '%00100010'],
    #                        remainder=None)

    # tkn = Token.create_using("SYMBOL",
    #                          args=['.label:'], remainder=tkn2)

    # print(tkn.__repr__())

    LINE = "SECTION 'Cool Stuff',ROMX[$4567],BANK[3]"
    token_group = Tokenizer().tokenize(LINE)
    print(token_group)

    # line = ".label: DB $FF,$00,$FF,$00,$FF,$00,$FF,$00,$FF,$00,$FF,$00,$FF"
    LINE = ".label: JP NZ, $0010"
    token_group = Tokenizer().tokenize(LINE)
    print(token_group)

    # *Python :: Run file from project directory
