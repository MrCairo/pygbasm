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
    _pointer = None
    _section_base = None

    def __init__(self):
        self._pointer = 0x0000
        self._section_base = 0x00

    def __repr__(self):
        desc = "No value"
        if self._pointer is not None:
            desc = f"Address: {self._pointer:04x}".upper()
        return desc

    @property
    def pointer(self) -> int:
        """Returns the current location or IP."""
        return self._pointer

    @pointer.setter
    def pointer(self, value):
        """Sets the current location or IP."""
        if value in range(0, 65536):
            #print(f"Setting IP to {hex(value)}")
            self._pointer = value

    def move_pointer_relative(self, val) -> bool:
        return self.move_location_relative(val)

    @property
    def location(self) -> int:
        """Returns the current location or IP."""
        return self._pointer

    @location.setter
    def location(self, value):
        """Sets the current location or IP."""
        if value in range(0, 65536):
            #print(f"IP(): Setting IP to {hex(value)}")
            self._pointer = value

    def move_location_relative(self, val) -> bool:
        """
        Moves the location (pointer) val distance positive or negative
        relative to the current location. If the move can be made within
        the range of 0 to 65535 then the return value will be True,
        otherwise it will be false.  This method differs from then
        move_relative() method in that the direction is not limited to +/-
        127/128.
        """
        newloc = self._pointer + val
        if 65536 > newloc >= 0:
            #print(f"IP(): Moving pointer {hex(val)} bytes. New Address = {hex(newloc)}")
            self._pointer = newloc
            return True
        return False

    @property
    def base_address(self):
        """Returns the base address of the current location.
        This is based upon the SECTION in which the IP is in.
        """
        return self._section_base

    @base_address.setter
    def base_address(self, new_value):
        """Sets the base address of this instruction pointer.
        This relates to the SECTION value that the IP is in.
        """
        # A value can be an expression such as $FFD2
        _conv = ExpressionConversion()
        address = _conv.value_from_expression(new_value)
        #print(f"IP: Setting Address to {hex(address)}")
        if address is None:
            address = 0x0000
        else:
            self._section_base = address
            self._pointer = address

    def offset_from_base(self) -> int:
        return self.location - self.base_address

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
            if self._pointer + displacement > 0:
                self._pointer += displacement
                rc = True
        return rc
