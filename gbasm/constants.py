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
MITCH = "MITCH"

DIRECTIVES = [
    "EQU", "SET", "SECTION", "EQUS", "MACRO", "ENDM", "EXPORT", "GLOBAL",
    "PURGE", "INCBIN", "UNION", "NEXTU", "ENDU"
]
STORAGE_DIR = ["DS", "DB", "DW", "DL"]


class Constants:
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
    MITCH = "MITCH"
    DIRECTIVES = [
        "EQU", "SET", "SECTION", "EQUS", "MACRO", "ENDM", "EXPORT", "GLOBAL",
        "PURGE", "INCBIN", "UNION", "NEXTU", "ENDU"
    ]
    STORAGE_DIR = ["DS", "DB", "DW", "DL"]


