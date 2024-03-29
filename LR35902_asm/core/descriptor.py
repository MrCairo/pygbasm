"""Various descriptors for generating validated numeric values."""


from abc import ABC, abstractmethod
import string
from dataclasses import dataclass
from .constants import MinMax


@dataclass
class DescriptorArgs():
    """The format that describes a value."""

    chars: MinMax
    limits: MinMax
    base: int
    charset: str

# |-----------------============<***>=============-----------------|


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


# |-----------------============<***>=============-----------------|


class BaseDescriptor(Validator):
    """A class that represents a value with n chars of min/max values."""

    bases = {
        0: f"{string.ascii_letters}{string.digits}_",  # Label Type
        2: "01",
        8: string.octdigits,
        10: string.digits,
        16: string.hexdigits}

    def __init__(self, chars: MinMax, limits: MinMax, base=10):
        """Initialie the object with # of chars and min/max values.

        chars represent the min and max nummber of characters.
        limits represents the base-10 min/max values of this object.
        A base of 0 is reserved for strings which can consist of any
        uppercase letter or numbers 0-9. No spaces or punctuation.
        """
        if base not in self.bases:
            raise TypeError(f'Base can only 2, 8, 10 or 16 but was {base}')
        self.args = DescriptorArgs(chars=chars,
                                   limits=limits,
                                   base=base,
                                   charset=self.bases[base])

    def charset(self) -> str:
        """Return the allowable characters for the object's base."""
        return self.args.charset

    def validate(self, value):
        """Validate this object against a specific value."""
        if not isinstance(value, str):
            raise TypeError(f'Expected {value!r} to be a str.')

        if all(c in self.args.charset for c in value) is False:
            raise ValueError(f"{value} bad base {self.args.base} chars.")

        # -- chars validation --
        (mini, maxi) = self.args.chars
        if len(value) not in range(mini, maxi):
            msg = f'{value} must be between {mini} and {maxi} chars'
            raise ValueError(msg)

        # -- limits validation value transformed to base-10 --
        dec_val = int(value, self.args.base)
        (mini, maxi) = self.args.limits
        if dec_val not in range(mini, maxi):
            raise ValueError(f'{dec_val} outside range of {mini}, {maxi}.')


# |-----------------============<***>=============-----------------|

DEC_DSC = BaseDescriptor(chars=MinMax(1, 6),
                         limits=MinMax(0, 65535),
                         base=10)
HEX_DSC = BaseDescriptor(chars=MinMax(2, 3),
                         limits=MinMax(0, 255),
                         base=16)
HEX16_DSC = BaseDescriptor(chars=MinMax(2, 5),
                           limits=MinMax(0, 65535),
                           base=16)
BIN_DSC = BaseDescriptor(chars=MinMax(2, 9),
                         limits=MinMax(0, 255),
                         base=2)
OCT_DSC = BaseDescriptor(chars=MinMax(1, 7),
                         limits=MinMax(0, 65535),
                         base=8)
LBL_DSC = BaseDescriptor(chars=MinMax(1, 16),
                         limits=MinMax(0, 0),
                         base=0)

# |-----------------============<***>=============-----------------|


class BaseValue:
    """Base class for a BaseDescriptor value."""

    _descr: BaseDescriptor
    _base: int
    _ftypes = {2: 'b', 8: 'o', 10: 'd', 16: 'X'}

    def __init__(self, desc: BaseDescriptor, value):
        """Initialize the base object."""
        # We need to save off the parms. The Validator's getter
        # will be called when accessing the _descr variable which will
        # return 'value' instead of the Validatior object.
        self._chars = desc.chars
        self._limits = desc.limits
        self._base = desc.base
        self._descr = BaseDescriptor(chars=desc.chars,
                                     limits=desc.limits,
                                     base=desc.base)
        self._descr = value  # Fails is value is invlaid for desc

    def __repr__(self):
        """Return a string representation of how re-create this object."""
        bd_str = f"BaseDescriptor(chars={self._chars}, "
        bd_str += f"limits={self._limits}, "
        bd_str += f"base={self._base})"
        vision = f"BaseValue({bd_str})"
        return vision

    def __str__(self):
        """Return a string representation of this object."""
        _val = int(self._descr, self._base)
        _max = self._chars.max - 1
        _format = self._ftypes[self._base]
        _filled = f"{_val:0{_max}{_format}}"
        return _filled

    def charset(self):
        """Return the set of valid characters for this object."""
        return self._descr.charset()

    def decimal_value(self):
        """Convert theobject to its decimial equivalent."""
        return int(self._descr, self._base)

# |-----------------============<***>=============-----------------|


class BinaryValue(BaseValue):
    """Represent a binary number value."""

    def __init__(self, value: str):
        """Initialize a Binary value descriptor."""
        super().__init__(BIN_DSC, value)


class DecimalValue(BaseValue):
    """Represent a decimial value of 0 - 65535."""

    def __init__(self, value: str):
        """Initialize a Decimal value descriptor."""
        super().__init__(DEC_DSC, value)


class Hex8Value(BaseValue):
    """Represent an 8-bit hex value."""

    def __init__(self, value: str):
        """Initialize a 8-bin Hexidecimal value descriptor."""
        super().__init__(HEX_DSC, value)


class Hex16Value(BaseValue):
    """Represent a 16-bit hex value."""

    def __init__(self, value: str):
        """Initialize a 16-bit Hexidecimal value descriptor."""
        super().__init__(HEX16_DSC, value)


class OctalValue(BaseValue):
    """Represent a 16-bit hex value."""

    def __init__(self, value: str):
        """Initialize an Octal value descriptor."""
        super().__init__(OCT_DSC, value)


class LabelValue(BaseValue):
    """Represent a string label value."""

    def __init__(self, value: str):
        """Initialize a string label value."""
        super().__init__(LBL_DSC, value)

#
# |-----------------============<***>=============-----------------|
#


if __name__ == "__main__":
    try:
        print(f'Decimal: {DecimalValue("255").decimal_value()}')
        print(OctalValue("100").decimal_value())
        print(OctalValue("100"))
        x = Hex16Value("E")
        print(x)
        print(x.decimal_value())
    except (ValueError, TypeError) as e:
        print(f"Failure: {e}")
