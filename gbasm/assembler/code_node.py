"""
Represents a single piece of code which could simply be a label
or an instruction. All code nodes put together can be used to
generate binary output of the compiled program.

The CodeNode object is designed so that it only records the offset value
from a specific location.
"""

from enum import IntEnum, auto
from collections import namedtuple
import tempfile
import pprint

import gbasm.core.constants as const

# class CodeLoc(namedtuple('CodeLoc', 'location, location_type')):
#     pass

class ReferenceType(IntEnum):
    IP_BASE = auto()
    IP_CURRENT = auto()
    LABEL = auto()
    ZERO = auto()
    NONE = auto()


CodeOffset_ = namedtuple("CodeOffset", "offset reference_frame reference_detail")
class CodeOffset(CodeOffset_):
    """
    Represents an offset value of a CodeNode. An Offset consists of
    an offset, a reference_frame, and optional reference_detail.

    Attributes:
        reference_frame (ReferenceType) represents what the offset
        is relative to.
    """
    pass


class CodeNode(object):
    """
    Represents a piece of code, label, or memory storage.
    Attributes:
        type: The const.NodeType of the code_obj which can be
              can be NODE, INS, LBL, etc. (See NoteType enum).
        code_obj: The actual code objed (i.e NODE, LBL, etc.)
        offset: A CodeOffset object representing the offset of
                of this object relative to something else
                (see CodeOffset obejct).
    """
    def __init__(self, type, code_obj, offset:CodeOffset):
        self.type = type
        self.code_obj = code_obj
        self.offset = offset

    def __str__(self):
        desc  = "\n"
        desc += f"CodeNode: {self.type_name}:\n"
        desc += f"   {self.code_obj.__str__()}\n"
        desc += f"   Offset: {self.offset.__str__()}\n"
        return desc

    @property
    def type(self) -> const.NodeType:
        """The const.NodeType value of the code_obj object"""
        return self._type

    @type.setter
    def type(self, new_value:const.NodeType):
        if new_value is not None and new_value in const.NODE_TYPES:
            self._type = new_value
        else:
            self._type = const.NodeType.NODE

    @property
    def type_name(self) -> str:
        """Returns the string representation of the const.NodeType."""
        if self.type in const.NODE_TYPES:
            return const.NODE_TYPES[self.type]
        return None

if __name__ == "__main__":
    import gbasm.core as core
    s = core.Storage.from_string("DB $00, $01, $01, $02, $03, $05, \
                            $08, $0d, 021, %00100010")
    x = CodeNode(const.STOR, s, 0x4000)
    print(s)
    print(x)
