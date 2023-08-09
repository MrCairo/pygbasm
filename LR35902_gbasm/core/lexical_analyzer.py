"""
Perform lexical analysis/parsing  and tokenization of a given buffer.

A directive that has been properly tokenized:
DB $0A, $0B, $0C
Becomes:
{
    'directive': 'STORAGE',
    'tokens': ['DB', '$0A', '$0B', '$0C'],
    'source_line': 6
}
'directive' is something like STORAGE, INSTRUCTION, SECTION
            (Shortcuts are STOR, INST, SEC and are defined in contants.py)
'tokens' is an array of values that represent the original source line
         broken up into individual 'tokens'. This makes parsing the value much
         simpler.
'source_line' is more of a convenience value that lets the system know
              which lin efrom the input stream this code has been read from.

"""
import pprint
from typing import List, Dict

from .reader import Reader, BufferReader
from .label import LabelUtils
from .exception import ErrorCode, Error
from .constants import DIRECTIVES, STORAGE_DIRECTIVES
from .constants import DIR, TOK, EXT, NODE, MULT, EQU, LBL, INST, STOR, SEC, BAD
from .registers import Registers
from .instruction_set import InstructionSet as IS
from .lexical_node import LexicalNode


class LexicalAnalyzer:
    """A class to analyze a set of lines of Z80 Assembler source code.
    The analyze_buffer and analyze_string are methods that provide a way
    to perform lexical analysis on a set of lines or a single line. The
    results of the lexical analysis are accumulated internally by default so
    as to represent a complete
    """
    def __init__(self):
        self._line_no = 0
        self._nodes: List[LexicalNode] = []
        self._pp = pprint.PrettyPrinter(indent=2, compact=False, width=40)
        self._notifications: List[Error] = []

    def analyze_buffer(self, reader: Reader, append=True) -> List[Dict]:
        """Analyzes the lines from the reader up to eof and returns the result
        as a list of lexical tokens. By default, the result is also appeded to
        the internal token list.

        Parameters:
        - reader (Reader): The Reader class to read the lines of text from.
        - append (bool): Keyword argument to indicate if the results of the
            lexical analysis are to be appended to the internal list of tokens
            or not. Default is True"""
        token_list: List[LexicalNode] = []
        while reader.is_eof() is False:
            line = reader.read_line()
            if len(line.strip()) == 0:
                continue
            try:
                node = self.analyze_string(line)
                self._line_no += 1 # As long as there is a line, count it.
                if node.directive() is None:
                    print("ERROR: Line could not be tokenized:")
                    print(line)
                    continue
                # tok['source_line'] = self._line_no
                token_list.append(node)
            except:
                err = Error(ErrorCode.INVALID_SYNTAX, f"Line: {line}")
                self._notifications.append(err)
        if append:
            self._nodes.extend(token_list)
        return token_list

    def analyze_string(self, line: str) -> LexicalNode:
        if line is None:
            return LexicalNode()
        if len(line) and line[0] == "*": # This is a line comment - ignore it.
            return LexicalNode()
        line = line.upper().split(";")[0].strip()  # drop comments
        if len(line) == 0:
            return LexicalNode()
        return LexicalAnalyzer._tokenize(line)

    def lexical_nodes(self) -> List[LexicalNode]:
        return self._nodes

    @classmethod
    def _tokenize(cls, line: str) -> LexicalNode:
        """
        Tokenizes a line of text into usable assembler chunks. Chunks are
        validated and a tokenized dictionary is returned.
        """
        clean = line.strip().split(';')[0]
        if not clean:
            return LexicalNode(None, None)  # Empy line
        tokens = {}
        clean = LexicalAnalyzer._join_parens(line)
        clean_split = clean.replace(',', ' ').split()
        if clean_split[0] in DIRECTIVES:
            tokens[DIR] = clean_split[0]
            tokens[TOK] = clean_split
        elif clean_split[0] in STORAGE_DIRECTIVES:
            tokens[DIR] = STOR
            tokens[TOK] = clean_split
        elif IS().is_mnemonic(clean_split[0]):
            tokens[DIR] = INST
            tokens[TOK] = clean_split
        elif line[0] in LabelUtils.valid_label_first_char():
            if LabelUtils.is_valid_label(clean_split[0]):
                tokens[DIR] = LBL
                if len(clean_split) > 1:
                    compound = [LexicalNode(LBL, clean_split[0])]
                    tokens[DIR] = MULT
                    remainder = ' '.join(clean_split[1:])
                    try:
                        more = LexicalAnalyzer._tokenize(remainder)
                        if more.directive() == LBL:
                            tokens[DIR] = BAD
                        compound.append(more)
                    except:
                        tokens[DIR] = BAD
                    # LBL that has a value that's also a LBL is invalid
                    tokens[TOK] = compound
                else:
                    tokens[TOK] = clean_split[0]
        if not tokens:
            tokens[DIR] = BAD
            tokens[TOK] = clean_split
        return LexicalNode(tokens[DIR], tokens[TOK])

    @classmethod
    def _join_parens(cls, line) -> str:
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

