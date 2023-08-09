"""
Commonly used constants
"""
import string
from enum import Enum, IntEnum, auto
from dataclasses import dataclass
from collections import namedtuple

DIR = "directive"
ORG = "origin"
TOK = "tokens"
EXT = "extra"
NODE = "node"  # Rpresents an internal tokenized node.
DEF = "DEFINE"
MULT = "MULTIPLE"
EQU = "EQU"
LBL = "LABEL"
SYM = "SYMBOL"
INST = "INSTRUCTION"
STOR = "STORAGE"
SEC = "SECTION"
BAD = "INVALID"

NodeType = Enum('NodeType', ['NODE',
                             'EQU',
                             'LBL',
                             'SYM',
                             'INST',
                             'STOR',
                             'SEC',
                             'ORG',
                             'DIR',
                             'DEF'])


NODE_TYPES = {
    NodeType.NODE: NODE,
    NodeType.EQU: EQU,
    NodeType.LBL: LBL,
    NodeType.SYM: SYM,
    NodeType.INST: INST,
    NodeType.STOR: STOR,
    NodeType.SEC: SEC,
    NodeType.ORG: ORG,
    NodeType.DEF: "DEFINE",
    NodeType.DIR: "directive"
}

AddressRange = namedtuple("AddressRange", ["start", "end"])


class AddressType(Enum):
    """Enumerate list of memory address types."""

    AbsolueAddress = auto()
    RelativeAddress = auto()


@dataclass
class NodeDefinition():
    """Hold the definition values of a Node for the compiler."""

    directive: str = "UNASSIGNED"
    identifier: str = None
    address_type: AddressType = AddressType.AbsolueAddress
    address_range: AddressRange = AddressRange(start=0, end=0)
    length: int = 0


# NODE_FORMAT = {
#     ORG: { "Directive": ORG,
#            "Identifier": None,  # String
#            "AddressType": AddressType.AbsolueAddress,
#            "Address": AddressSpread}
#     EQU: {}
# }
LOGGER_FORMAT = '[%(levelname)s] %(asctime)s - %(message)s'

DIRECTIVES = [
    "EQU",
    "SET",
    "SECTION",
    "EQUS",
    "MACRO",
    "ENDM",
    "EXPORT",
    "GLOBAL",
    "PURGE",
    "INCBIN",
    "UNION",
    "NEXTU",
    "ENDU",
    "DEF",
    "ORG"
]

STORAGE_DIRECTIVES = ["DS", "DB", "DW", "DL"]


class Lexical(IntEnum):
    """Lexical error types."""

    warning = 1
    syntax_error = 2
    unknown_error = 3


"""
$$        :4 digit hex value only.
' or "    :A string value but must begin and end with the same character.
$ and 0x  :2 digit hex value (0 - FF) only.
"""
VALUE_PREFIXES = ['$$', '$', '0x', '0', '"', "'", '%', '&']

MinMax = namedtuple("MinMax", ['min', 'max'])


@dataclass
class ValueDescriptor():
    """The format that describes a value."""

    length_limits: MinMax
    value_limits: MinMax
    value_base: int
    charset: str


DEC_DESCR = ValueDescriptor(MinMax(0, 5), MinMax(0, 65535), 10,
                            string.digits)
HEX_DESCR = ValueDescriptor(MinMax(0, 2), MinMax(0, 255), 16,
                            string.hexdigits)
HEX16_DESCR = ValueDescriptor(MinMax(0, 4), MinMax(0, 65535), 16,
                              string.hexdigits)
BIN_DESCR = ValueDescriptor(MinMax(2, 8), MinMax(0, 255), 2,
                            "01")
OCT_DESCR = ValueDescriptor(MinMax(0, 6), MinMax(0, 65535), 8,
                            string.octdigits)
STR_DESCR = ValueDescriptor(MinMax(1, 15), MinMax(0, 0), 0,
                            f"{string.ascii_uppercase}{string.digits}")
