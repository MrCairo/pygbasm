"""
Class that assigns a name to a constant.
"""

from enum import IntEnum, auto


class DefValueType(IntEnum):
    """Represents a DEF or Defined value"""
    string = auto()
    integer = auto()
    boolean = auto()


class Define():
    _name = None
    _value = None
    _type = None

    def __init__(self, name: str, value_str: str, value_type: DefValueType):
        """Initializes a DEF with name and value"""
        self._name = name
        self._value = value_str
        self._type = value_type

    def __str__(self):
        """Retrurns a string representation of the DEF"""
        return f"DEF \"{self._name}\" \"{self._value}\""

    def
