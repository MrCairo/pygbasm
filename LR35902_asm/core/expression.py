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

from .descriptor import HEX_DSC, HEX16_DSC, BIN_DSC, OCT_DSC, DEC_DSC, \
    LBL_DSC, BaseDescriptor

from .exception import ExpressionSyntaxError, ExpressionBoundsError


class ExpressionType(StrEnum):
    """The expression type."""

    BINARY = 'binary'
    CHARACTER = 'character'
    DECIMAL = 'decimal'
    HEXIDECIMAL = 'hexidecimal'
    INVALID = 'invalid'
    OCTAL = 'octal'

# |-----------------============<***>=============-----------------|


# It's important what order the prefixes appear in the array.  The '0x', for
# example, should be found before '0'. By doing this, we reduce the
# additional validation. If the array were defined with '0' first, there
# would need to be another check to see if there is an 'x' following the 0
# or if it's just 0 (decimal vs. hex definition).


class Expression():
    """Parse and categorize a numerical expression."""

    def __init__(self, value: str):
        """Initialize an Expression object with a specific value."""
        self._validate(value)

    def __repr__(self):
        """Return a representation of this object and how to re-create it."""
        return f"Expression({self._raw_value}"

    def __str__(self):
        """Return a String representation of the object."""
        if self._value_descr is None:
            return "Not initialized."
        desc = f"Type = {self._type}, Prefix = {self._prefix}"
        desc += f"Orignal: [{self._raw_value}]"
        return desc

    def _get_prefix(self) -> str:
        _prefixes = ["0x", "0", "$$", "$", "&", "%", "'", '"']
        _key = [x for idx, x
                in enumerate(_prefixes)
                if self._raw_value.startswith(_prefixes[idx])]

        if _key is None or len(_key) == 0:
            msg = f"Invalid Value: [{self._raw_value}]"
            raise ExpressionSyntaxError(msg)

        return _key[0]

    def _validate(self, value: str) -> bool:
        """Return the descriptor and expression type of the value passed."""
        # Record the original cleaned value first - called the raw value.
        self._raw_value = value.strip()

        if len(self._raw_value) < 3:  # 3 is the min size of an expression.
            msg = f"Invalid value length. Must be > 3: [{self._raw_value}]"
            raise ExpressionSyntaxError(msg)

        self._prefix = self._get_prefix()

        match self._prefix:
            case "$" | "0x":
                if len(self._raw_value[len(self._prefix):]) == 4:
                    descriptor = HEX16_DSC
                else:
                    descriptor = HEX_DSC
                expr_type = ExpressionType.HEXIDECIMAL
            case "$$":
                descriptor = HEX16_DSC
                expr_type = ExpressionType.HEXIDECIMAL
            case "0":
                descriptor = DEC_DSC
                expr_type = ExpressionType.DECIMAL
            case '"' | "'":
                descriptor = LBL_DSC
                expr_type = ExpressionType.CHARACTER
            case "%":
                descriptor = BIN_DSC
                expr_type = ExpressionType.BINARY
            case "&":
                descriptor = OCT_DSC
                expr_type = ExpressionType.OCTAL
            case _:
                msg = f"Expression prefix is invalid [{self._raw_value}]"
                raise ExpressionSyntaxError(msg)

        valid = self._extract_value(descriptor)
        if valid is not None:
            self._value_descr = descriptor
            self._type = expr_type
            self._value = valid
            return True

        return False

    # |-----------------============<***>=============-----------------|
    #                          Private Functions
    #
    # Extract and reyurn the value of the expression. This is the value that
    # remains once the prefix (and suffix for CHARACTER descriptors) are
    # removed. This makes it easier to process this expression later in the
    # compilation process.
    #
    # Examples:
    # $FF becomes FF, "Hello" becomes Hello
    #
    # ExpressionSyntaxError or ExpressionBoundsError can be thrown with
    # messages approapriate to the error.
    #
    def _extract_value(self, descr: BaseDescriptor) -> str:
        expr = self._raw_value
        raw = expr[len(self._prefix):]

        # Validate that the key passed is equal to the key of the expression.
        # (i.e. key of "$" is valud with an expression of "$1000".
        self._try_key_length()

        # value_base of 0 indicates a CHARACTER (string) expression.
        if descr.base == 0:
            self._try_str_term()
            # Drop trailing term char.
            raw = expr[len(self._prefix):len(expr)-1]

        # If any characters are NOT in the allowed charactset, fail.
        self._try_in_charset(descr)

        # Our range is inclusive of the max whereas the Python range()
        # is exclusive. The +1 over the limit accounts for this.
        self._try_len_range(descr)

        # LBL_DSC has a base of 0 so don't check min/max value here.
        if descr.value_base > 0:
            self._try_val_range(raw, expr, descr)
        return raw

    # |-----------------============<***>=============-----------------|
    #
    # Validation Functions
    #
    def _try_len_range(self, descr: BaseDescriptor):
        raw = self._raw_value[len(self._prefix):]
        if len(raw) not in range(descr.limits.min,
                                 descr.limits.max+1):
            msg = f"Expression length is outside predefined bounds: [{raw}]"
            raise ExpressionBoundsError(msg)

    def _try_val_range(self, raw: str, expr: str, descr: BaseDescriptor):
        num = int(raw, descr.base)
        if descr.limits.min > num > descr.limits.max:
            msg = "Expression value is outside predefined bounds: "
            msg += f"[{expr}]"
            raise ExpressionBoundsError(msg)

    def _try_in_charset(self, raw: str, expr: str, descr: BaseDescriptor):
        bad = [x for x in raw if x not in descr.charset()]
        if len(bad):
            msg = f"Invalid character in expression: [{expr}:{bad}]"
            raise ExpressionSyntaxError(msg)

    def _try_key_length(self, key: str, expr: str):
        if not expr or expr[:len(key)] != key:
            msg = f"Missing or invalid prefix: [{expr}]"
            raise ExpressionSyntaxError(msg)

    def _try_str_term(self, key: str, expr: str):
        if not expr.endswith(key):
            msg = f"Unterminated string: [{expr}]"
            raise ExpressionSyntaxError(msg)


# |-----------------============<***>=============-----------------|

# expression.py ends here.
