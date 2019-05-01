"""
A set of helper functions used during processing of instructions.
"""
from singleton_decorator import singleton
from gbasm.conversions import ExpressionConversion

###############################################################################
# Manages the instruction pointer position. Nececesary to compute
# label locations.
##
@singleton
class InstructionPointer():
    """ Represents the CPU's IP """
    __pointer = None
    __section_base = None

    def __init__(self):
        self.__pointer = 0x0000
        self.__section_base = 0x00

    def __repr__(self):
        desc = "No value"
        if self.__pointer is not None:
            desc = f"Address: {self.__pointer:04x}".upper()
        return desc

    @property
    def location(self) -> int:
        """Returns the current location or IP."""
        return self.__pointer

    @location.setter
    def location(self, value):
        """Sets the current location or IP."""
        if value in range(0, 65536):
            self.__pointer = value

    @property
    def base_address(self):
        """Returns the base address of the current location.
        This is based upon the SECTION in which the IP is in.
        """
        return self.__section_base

    @base_address.setter
    def base_address(self, new_value):
        """Sets the base address of this instruction pointer.
        This relates to the SECTION value that the IP is in.
        """
        # A value can be an expression such as $FFD2
        _conv = ExpressionConversion()
        address = _conv.value_from_expression(new_value)
        if address is None:
            address = 0x0000
        else:
            self.__section_base = address
            self.__pointer = address

    def move_relative(self, relative):
        """
        relative is a single byte. 0 - 127 is positive branch
        128 - 255 is negative branch. The relative value must be
        a positive number from 0 - 255.
        """
        rc = False
        if relative in range(0, 255):
            neg = relative >> 7
            displacement = ((relative ^ 255) + 1) * -1 if neg else relative
            if self.__pointer + displacement > 0:
                self.__pointer += displacement
                rc = True
        return rc
