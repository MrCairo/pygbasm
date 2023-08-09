"""A numeric or string value expression.

Represents a validated expression.
An expression is like:
    0xFFFF
    $AABC
    %010101
    &1777
    "MY_LABEL"
"""
from enum import StrEnum
from .exception import ExpressionSyntaxError, ExpressionBoundsError
from .constants import \
    ValueDescriptor, DEC_DESCR, HEX_DESCR, HEX16_DESCR, \
    BIN_DESCR, OCT_DESCR, STR_DESCR, VALUE_PREFIXES

_prefixes = VALUE_PREFIXES


class ExpressionType(StrEnum):
    """The expression type."""

    BINARY = 'binary'
    CHARACTER = 'character'
    DECIMAL = 'decimal'
    HEXIDECIMAL = 'hexidecimal'
    INVALID = 'invalid'
    OCTAL = 'octal'

# |-----------------============<***>=============-----------------|


"""
    It's important what order the prefixes appear in the array.  The '0x', for
    example, should be found before '0'. By doing this, we reduce the
    additional validation. If the array were defined with '0' first, there
    would need to be another check to see if there is an 'x' following the 0
    or if it's just 0 (decimal vs. hex definition).
"""


class Expression():
    """Represent a validated expression given a plain string."""

    _raw_value: str = None
    _value_descr: ValueDescriptor = None
    _prefix: str = None
    _type: ExpressionType = ExpressionType.INVALID

    def __init__(self, expression: str):
        """Initialize an Expression object given a plain string."""
        if expression is None:
            raise ExpressionSyntaxError("Missing expression string value")

        self._str_exp = expression.strip()
        self._len = len(self._str_exp)
        self._raw_value = None
        try:
            self._process()
        except ExpressionSyntaxError as fail_msg:
            raise ExpressionSyntaxError(fail_msg)
        except ExpressionBoundsError as fail_msg:
            raise ExpressionBoundsError(fail_msg)

    # ------------------------------
    @property
    def raw_value(self):
        """Return the value string without a prefix or suffix character."""
        return self._raw_value

    # ------------------------------
    @property
    def descriptor(self):
        """Return the ValueDescriptor object that defines this expression."""
        return self._value_descr

    # ------------------------------
    @property
    def prefix(self):
        """The prefix of the expression."""
        return self._prefix

    # ------------------------------
    @property
    def type(self):
        """The validated type of this expression."""
        return self._type

    # ------------------------------
    def to_decimal(self):
        """Convert the Expression to a decimal value."""
        num = None
        if self.descriptor.value_base > 0:
            num = int(self.raw_value, self.descriptor.value_base)
        return num

    # ------------------------------
    def _process(self):
        found = [x for x in _prefixes if self._str_exp.startswith(x)]
        key = found[0] if len(found) else None
        descriptor = None
        expr_type = None

        match key:
            case "$" | "0x":
                if self._len == 5:
                    descriptor = HEX16_DESCR
                else:
                    descriptor = HEX_DESCR
                expr_type = ExpressionType.HEXIDECIMAL
            case "$$":
                descriptor = HEX16_DESCR
                expr_type = ExpressionType.HEXIDECIMAL
            case "0":
                descriptor = DEC_DESCR
                expr_type = ExpressionType.DECIMAL
            case '"':
                descriptor = STR_DESCR
                expr_type = ExpressionType.CHARACTER
            case "%":
                descriptor = BIN_DESCR
                expr_type = ExpressionType.BINARY
            case "&":
                descriptor = OCT_DESCR
                expr_type = ExpressionType.OCTAL
            case _:
                return False

        valid = self._check_exp(key, descriptor)
        if valid is not None:
            self._value_descr = descriptor
            self._prefix = key
            self._raw_value = valid
            self._type = expr_type
            return True

        return False

    # |-----------------============<***>=============-----------------|
    #                          Private Functions
    #
    # Return the raw value of the expression if it is a valid expression
    # otherwise an exception is thrown that describes the error.
    #
    # ExpressionSyntaxError or ExpressionBoundsError can be thrown with
    # messages approapriate to the error.
    #
    def _check_exp(self, key, descr: ValueDescriptor) -> str:
        expr = self._str_exp
        raw = expr[len(key):]

        # Validate that the key passed is equal to the key of the expression.
        # (i.e. key of "$" is valud with an expression of "$1000".
        _try_key_length(key, expr)

        # value_base of 0 indicates a CHARACTER (string) expression.
        if descr.value_base == 0:
            _try_str_term(key, expr)
            raw = expr[len(key):len(expr)-1]  # Drop trailing term char.

        # If any characters are NOT in the allowed charactset, fail.
        _try_in_charset(raw, expr, descr)

        # Our range is inclusive of the max whereas the Python range()
        # is exclusive. The +1 over the limit accounts for this.
        _try_len_range(raw, expr, descr)

        # STR_DESCR has a base of 0 so don't check min/max value here.
        if descr.value_base > 0:
            _try_val_range(raw, expr, descr)

        return raw

# |-----------------============<***>=============-----------------|
#
# Validation Functions
#


def _try_len_range(raw: str, expr: str, descr: ValueDescriptor):
    if len(raw) not in range(descr.length_limits.min,
                             descr.length_limits.max+1):
        msg = f"Expression length is outside predefined bounds: [{expr}]"
        raise ExpressionBoundsError(msg)


def _try_val_range(raw: str, expr: str, descr: ValueDescriptor):
    num = int(raw, descr.value_base)
    if descr.value_limits.min > num > descr.value_limits.max:
        msg = f"Expression value is outside predefined bounds: [{expr}]"
        raise ExpressionBoundsError(msg)


def _try_in_charset(raw: str, expr: str, descr: ValueDescriptor):
    bad = [x for x in raw if x not in descr.charset]
    if len(bad):
        msg = f"Invalid character in expression: [{expr}:{bad}]"
        raise ExpressionSyntaxError(msg)


def _try_key_length(key: str, expr: str):
    if not expr or expr[:len(key)] != key:
        msg = f"Missing or invalid prefix: [{expr}]"
        raise ExpressionSyntaxError(msg)


def _try_str_term(key: str, expr: str):
    if not expr.endswith(key):
        msg = f"Unterminated string: [{expr}]"
        raise ExpressionSyntaxError(msg)


# |-----------------============<***>=============-----------------|
# expression.py ends here.
