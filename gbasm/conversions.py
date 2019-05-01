#
# ExpressionConversion
#
import string
from singleton_decorator import singleton
from gbasm.constants import Constant

@singleton
class ExpressionConversion():
    """Class to convert a numeric type from one base to/from decimal.
    When an expression is provided or requested, it will have one of
    these previx values:

    '$' -- Hex value. If the decimal value is less than 256, the value
           returned will be a single byte.

    '$$' -- Hex value and input only. The decimal value is always
            returned as a 16-bit value regardless if the decimal value
            is less than 256.

    '0' -- A decimal value

    '%' -- A binary value.
    """
    _instance = None
    _to_dec = None

    def __init__(self):
        self._to_dec = {
            '$': self._hex_to_dec,
            '0': self._dec,
            '%': self._bin_to_dec,
            '&': self._oct_to_dec
        }
        self._from_dec = {
            '$': self._dec_to_hex,
            '$$': self._dec_to_hex16,
            '0': self._dec_to_dec,
            '%': self._dec_to_bin,
            '&': self._dec_to_oct
        }
        self._8_bit_registers = ['B', 'C', 'D', 'E', 'H', 'L', 'A']
        self._16_bit_registers = ['BC', 'DE', 'HL', 'F', 'PC', 'SP']

    def expression_from_value(self, dec_value, expression_prefix) -> str:
        """Returns a converted decimal value based upon the specified prefix.
        expression_prefix -- This represents the data type to convert the
        provided decimal value to.
        """
        try:
            dec_value = dec_value + 0  # Ensure that this is a numeric value
        except TypeError:
            return ""

        if expression_prefix in self._from_dec:
            conv = self._from_dec[expression_prefix]
            return conv(dec_value)
        return ""

    def value_from_expression(self, expression: str):
        """
        Returns a decimal value from the given numeric string
        expression.
        Hexadecimal: $0123456789ABCDEF. Case-insensitive
        Decimal: 0123456789
        Octal: &01234567
        Binary: %01
        Fixedpoint (16.16): 01234.56789
        Character constant: "ABYZ"
        Gameboy graphics: '0123
        """
        if not expression:
            return None

        key = expression[:1]
        # A little flexibility:
        # If we see a number like 150 then treat it like a decimal number
        # instead of failing.
        if expression[0].isdigit() and expression[0] != "0":
            key = "0"
            expression = "0" + expression
        conv = None if key not in self._to_dec else self._to_dec[key]
        if conv:
            return conv(expression)
        return None

    def placeholder_from_expression(self, expression: str):
        """
        Returns a placeholder value indicating whether or not the
        value is an 8 or 16 bit value. This placeholder is used
        when looking up an instruction in the InstructionSet class
        (i.e. 'JP NZ, a16' is recognized, 'JR NZ, $FFD2' is not)
        """
        # If the expression is in the form of $0001 then this will
        # always resolve to a 16-bit address even though the value
        # is in the 8-bit range. Two digit expressions (like $80)
        # will always resolve to an 8-bit value.
        #
        # if not expression:
        #     return None

        # if self._is_register(expression):
        #     if len(expression) == 2:
        #         return Constant.PLACEHOLDER_16
        #     return Constant.PLACEHOLDER_8

        # if self._is_hex(expression):
        #     return Constant.PLACEHOLDER_16 if len(expression) > 3 \
        #         else Constant.PLACEHOLDER_8

        # if expression[0].isdigit():
        #     test = self._dec(expression)
        #     if test is None:
        #         return None

        # # Everything other than hex values below....
        # value = self.value_from_expression(expression)
        # if value:
        #     if value in range(0, 255):
        #         return "{8}"
        #     if value in range(256, 65535):
        #         return "{16}"
        return None

    def can_convert(self, expression):
        """Returns the decimal equivalent of 'expression' or None if it can't
        be converted.
        """
        return self.value_from_expression(expression) is not None

    def has_valid_prefix(self, expression):
        """Returns True if the prefix of the expression is a supported prefix,
        False otherwise."""
        valid = False
        if expression:
            val = expression[0]
            valid = val in self._to_dec.keys()
            valid |= val in self._from_dec.keys()
            valid |= val in string.digits
        return valid

    # def hex_to_high_low(self, hex_value):
    #     new_value = None
    #     dec = self._hex_to_dec(hex_value)
    #     if dec is not None:
    #         high = dec & 0xff00
    #         low = dec & 0x00ff
    #         new_value = self._dec_to_hex(high)
    #         new_value = self._dec_to_hex
    #     return new_value

    # def hex_high_byte(self, hex_value):
    #     new_value = None
    #     dec = self._hex_to_dec(hex_value)
    #     if dec is not None:
    #         new_value = self._dec_to_hex16(dec & 0xff00)
    #     return new_value

    def _hex_to_dec(self, val):
        """
        Convert a hexidecimal number ($12, $1234) into a decimal value
        """
        hexi = "0123456789ABCDEF"
        if not self._validate_expression(val, '$', 2, 10, hexi):
            return None

        return int(val[1:], 16)

    def _dec_to_hex(self, val, digits=2):
        """Converts a decimal value into it's hexidecimal equivalent."""
        try:
            clean = val + 0
        except TypeError:
            return None
        # Validate ranges
        if digits not in [2, 4]:
            digits = 2
        if clean < 0:
            clean = 0
        if clean > 255:
            digits = 4
        if clean >= 16 ** digits:
            clean = (16 ** digits) - 1
        hex_str = hex(clean)[2:]
        padded = "$" + hex_str.zfill(digits)
        return padded

    def _dec_to_hex16(self, val):
        """Returns a decimal value into it's 16-bit decimal equivalent"""
        return self._dec_to_hex(val, digits=4)

    def _dec(self, val):
        """Validate and return the value as a decimal number"""
        if not self._validate_expression(val, '0', 1, 10, "0123456789"):
            return None

        return int(val[1:], 10)

    def _dec_to_dec(self, val):
        """
        Returns a decimal value as a string with a leading 0 (123 = 0123). This
        is used primarily to convert a value as it would appear as an
        expression. Like a hex value starts with '$', a decimal value starts
        with '0'.
        """
        try:
            clean = max(0, min(65535, val))
        except TypeError:
            return None
        return "0" + str(clean)

    def _bin_to_dec(self, val):
        """
        Validate the binary value and return as a decimal number.
        The binary value (%1001) can be from 1 bit to a max of 16 bits.
        """
        if not self._validate_expression(val, '%', 1, 16, "01"):
            return None

        return int(val[1:], 2)

    def _dec_to_bin(self, val):
        """ Returns the binary representation of the provided decimal value.
            Returns a 0 if < 0, 65535 if > 65535
        """
        clean = max(0, min(65535, val))
        return '%' + bin(clean)[2:]

    def _oct_to_dec(self, val):
        """
        Validate the octal value and return as a decimal number.
        The binary value (%1001) can be from 1 bit to a max of 16 bits.
        """
        if not self._validate_expression(val, '&', 1, 5, "01234567"):
            return None

        return int(val[1:], 8)

    def _dec_to_oct(self, val):
        """Converts the decimal value to it's Octal equivalent."""
        try:
            clean = max(0, min(65535, val))
        except TypeError:
            return None
        return '&' + oct(clean)[2:]

    def _validate_expression(self, exp, key, mini, maxi, chrset):
        if not exp or exp[:1] != key:
            return False

        val = exp[1:]
        if len(val) < mini or len(val) > maxi:
            return False

        for char in val:
            if char.upper() not in chrset:
                return False
        return True

    def _is_hex(self, expression):
        if expression:
            return expression.strip()[0] == "$"
        return False

    #
    # Kind of a dup of the InstructionSet().is_valid_register() function.
    # Probably move the InstructionSet one to here since we don't want
    # instruction.py and conversions.py to cross reference each other.
    #
    def _is_register(self, expression):
        is_reg = False
        if expression:
            upcase = expression.upper()
            if upcase in self._8_bit_registers:
                is_reg = True
            elif upcase in self._16_bit_registers:
                is_reg = True
        return is_reg

# End of class ExpressionConversion #


if __name__ == "__main__":
    print(ExpressionConversion().value_from_expression("$ffff"))
