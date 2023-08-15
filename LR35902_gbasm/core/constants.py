"""Commonly used constants."""

import string
from enum import Enum, IntEnum, auto
from dataclasses import dataclass
from collections import namedtuple

# Token Element Names
ARGS = "arguments"
BAD = "invalid"
DIR = "directive"
PARM = "parameters"
REMN = "remainder"
TOK = "tokens"
TELM = "telemetry"  # Location specific information
NODE = "node"  # Rpresents an internal tokenized node.


#  Code-level element names
DEF = "DEFINE"
EQU = "EQU"
INST = "INSTRUCTION"
LBL = "LABEL"
MULT = "MULTIPLE"
ORG = "ORIGIN"
SEC = "SECTION"
STOR = "STORAGE"
SYM = "SYMBOL"

NodeType = Enum('NodeType', ['DEF',    # Define
                             'DIR',    # Directive (generic)
                             'EQU',    # Equate
                             'INST',   # Instruction
                             'LBL',    # Label
                             'ORG',    # Origin
                             'PARM',   # Parameter
                             'SEC',    # Section
                             'STOR',   # Storage
                             'SYM',    # Symbol
                             'NODE'])  # Node


NODE_TYPES = {
    NodeType.NODE: NODE,
    NodeType.EQU: EQU,
    NodeType.LBL: LBL,
    NodeType.SYM: SYM,
    NodeType.PARM: PARM,
    NodeType.INST: INST,
    NodeType.STOR: STOR,
    NodeType.SEC: SEC,
    NodeType.ORG: ORG,
    NodeType.DEF: DEF,
    NodeType.DIR: DIR
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
    "DB",  # Storage
    "DEF",
    "DL"   # Storage
    "DS",  # Storage
    "DW",  # Storage
    "ENDM",
    "ENDU",
    "EQU",
    "EQUS",
    "EXPORT",
    "GLOBAL",
    "INCBIN",
    "MACRO",
    "NEXTU",
    "ORG",
    "Purge",
    "SECTION",
    "SET",
    "UNION",
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


#
# DESCR is shorthand for Descriptor
#
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
