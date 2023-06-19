"""
Commonly used constants
"""
from enum import Enum, IntEnum

DIR = "directive"
TOK = "tokens"
EXT = "extra"
NODE = "node"  # Rpresents an internal tokenized node.
MULT = "MULTIPLE"
EQU = "EQU"
LBL = "LABEL"
INST = "INSTRUCTION"
STOR = "STORAGE"
SEC = "SECTION"
BAD = "INVALID"

class NodeType(Enum):
    NODE = 1
    EQU = 2
    LBL = 3
    INST = 4
    STOR = 5
    SEC = 6
    DIR = 7

NODE_TYPES = {
    NodeType.NODE: NODE,
    NodeType.EQU: EQU,
    NodeType.LBL: LBL,
    NodeType.INST: INST,
    NodeType.STOR: STOR,
    NodeType.SEC: SEC,
    NodeType.DIR: DIR
}

DIRECTIVES = [
    "EQU", "SET", "SECTION", "EQUS", "MACRO", "ENDM", "EXPORT", "GLOBAL",
    "PURGE", "INCBIN", "UNION", "NEXTU", "ENDU"
]

STORAGE_DIRECTIVES = ["DS", "DB", "DW", "DL"]

class Lexical(IntEnum):
    warning = 1
    syntax_error = 2
    unknown_error = 3

