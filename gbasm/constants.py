"""
Commonly used constants
"""
DIR = "directive"
TOK = "tokens"
NODE = "node"  # Rpresents an internal tokenized node.
MULT = "MULTIPLE"
EQU = "EQU"
LBL = "LABEL"
INST = "INSTRUCTION"
STOR = "STORAGE"
SEC = "SECTION"

DIRECTIVES = ["EQU", "SET", "SECTION", "EQUS", "MACRO", "ENDM",
              "EXPORT", "GLOBAL", "PURGE", "INCBIN", "UNION",
              "NEXTU", "ENDU"]
STORAGE_DIR = ["DS", "DB", "DW", "DL"]
