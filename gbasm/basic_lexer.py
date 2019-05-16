"""
Z80 Assembler
"""
from gbasm.reader import Reader, BufferReader
from gbasm.instruction import InstructionSet
from gbasm.label import is_valid_label, valid_label_chars
from gbasm.label import valid_label_first_char
from gbasm.constants import DIR, TOK, MULT, STOR, INST, LBL


IS = InstructionSet

class BasicLexer:
    _file_name: str
    _line_no: int = 0
    _reader: Reader
    _tokenized: list = []

    def __init__(self, reader: Reader):
        self._reader = reader
        self._file_name = reader.filename

    @classmethod
    def from_text(cls, text: str):
        "Tokenize using a buffer of text."
        reader = BufferReader(text)
        return cls(reader)

    def tokenize(self):
        """Tokenizes the the Reader starting at the current read position."""
        while self._reader.is_eof() is False:
            line = self._reader.read_line()
            if line:
                line = line.upper().split(";")[0]  # drop comments
                if not line:
                    continue
                self._line_no += 1
                tokens = BasicLexer._tokenize_line(line)
                tokens['source_line'] = self._line_no
                self._tokenized.append(tokens)

    def tokenized_list(self):
        return self._tokenized

    # -----=====< End of section >=====----- #

    @staticmethod
    def _join_parens(line) -> str:
        new_str = ""
        paren = 0
        for c in line:
            if c == " " and paren > 0:
                continue
            if c in "([{":
                paren += 1
            elif c in ")]}":
                paren -= 1
            paren = max(0, paren) # If Negative set to 0
            new_str += c
        return new_str

    @staticmethod
    def _tokenize_line(line) -> dict:
        clean = line.strip().split(';')[0]
        if not clean:
            return None  # Empy line
        directives = ['EQU', 'SET', 'SECTION', 'EQUS', 'MACRO', 'ENDM',
                      'EXPORT', 'GLOBAL', 'PURGE', 'INCBIN', 'UNION',
                      'NEXTU', 'ENDU']
        tokens = {}
        clean = BasicLexer._join_parens(line)
        clean_split = clean.replace(',', ' ').split()
        if clean_split[0] in directives:
            tokens[DIR] = clean_split[0]
            tokens[TOK] = clean_split
            return tokens
        if clean_split[0] in ["DS", "DB", "DW", "DL"]:
            tokens[DIR] = STOR
            tokens[TOK] = clean_split
            return tokens
        if IS().is_mnemonic(clean_split[0]):
            tokens[DIR] = INST
            tokens[TOK] = clean_split
            return tokens
        if line[0] in valid_label_first_char():
            if is_valid_label(clean_split[0]):
                tokens[DIR] = LBL
                data = clean_split
                if len(clean_split) > 1:
                    data = [{DIR: LBL, TOK: clean_split[0]}]
                    tokens[DIR] = MULT
                    remainder = ' '.join(clean_split[1:])
                    more = BasicLexer._tokenize_line(remainder)
                    data.append(more)
                tokens[TOK] = data
                return tokens
        tokens[DIR] = "UNKNOWN"
        tokens[TOK] = clean.split()
        return tokens

    # --------========[ End of class ]========-------- #


def is_node_valid(node: dict) -> bool:
    """
    Returns True if the provided node contains a directive and token.
    """
    result = False
    if node:
        if DIR in node and TOK in node:
            result = True
    return result

def is_multiple_node(node: dict) -> bool:
    """
    Returns True if the provided node is valid and contains other nodes
    with the 'tokens' key.
    """
    if not is_node_valid(node):
        return False
    nodes = None
    result = False
    if node[DIR] == MULT:
        nodes = node[TOK]
    if nodes:
        for n in nodes:
            result = is_node_valid(n)
            if not result:
                break
    return result
