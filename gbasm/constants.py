"""
Commonly used constants
"""
from enum import Enum

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

STORAGE_DIR = ["DS", "DB", "DW", "DL"]

# class Constants:
#     DIR = "directive"
#     TOK = "tokens"
#     EXT = "extra"
#     NODE = "node"  # Rpresents an internal tokenized node.
#     MULT = "MULTIPLE"
#     EQU = "EQU"
#     LBL = "LABEL"
#     INST = "INSTRUCTION"
#     STOR = "STORAGE"
#     SEC = "SECTION"
#     MITCH = "MITCH"
#     DIRECTIVES = [
#         "EQU", "SET", "SECTION", "EQUS", "MACRO", "ENDM", "EXPORT", "GLOBAL",
#         "PURGE", "INCBIN", "UNION", "NEXTU", "ENDU"
#     ]
#     STORAGE_DIR = ["DS", "DB", "DW", "DL"]


