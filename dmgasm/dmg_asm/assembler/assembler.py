"""
Z80 Assembler
"""
from enum import IntEnum, auto
from typing import List
from collections import namedtuple
import tempfile
import pprint

from core import InstructionSet, InstructionPointer, ExpressionConversion
from core import FileReader, BufferReader, BasicLexer
from core import NODE, INST, is_node_valid, is_compound_node
from code_node import CodeNode, CodeOffset, ReferenceType
from node_processor import NodeProcessor


class Action(IntEnum):
    """The current state of the parser state machine."""
    INITIAL = auto()
    UNDETERMINED = auto()
    SECTION = auto()
    EQU = auto()
    STORAGE = auto()
    CODE = auto()
    IGNORE = auto()


class ParserState(IntEnum):
    IDLE = auto()
    RESOLVE = auto()
    ASSEMBLE = auto()


EC = ExpressionConversion
IS = InstructionSet
IP = InstructionPointer


"""
Need to create some global/local storage (like global.py is now). There
needs to be a way to identify file-local labels/variables, etc. as well as
global ones. If a file is 'imported' it could very well define it's own
local variables as opposed to the file that did the importing. Everything
is based around the Parser class. Whenever a file is opened, it is
processed via the Parser class. If the Parser detects an import, that file
is then opened and another (nested) Parser class is instantiated again, and
so on.
"""


class Assembler:
    """The main entrypoint (class) to instantiate in order to compile any
    Z80 source."""

    def __init__(self):
        self.filename = None
        self.reader = None
        self.line_no = 0
        self._parser = None
        self.code: List[CodeNode] = []
        self.lexer = None
        self._np = None

    def load_from_file(self, filename):
        """Loads the assembly program from a file."""
        self.filename = filename
        self.reader = FileReader(filename)
        self.lexer = BasicLexer(self.reader)

    def load_from_buffer(self, buffer_in):
        """Loads the assembly program from a memory buffer."""
        self.reader = BufferReader(buffer_in)
        self.lexer = BasicLexer(self.reader)

    def parse(self):
        """Starts the assembler's parser."""
        self._np = NodeProcessor(self.reader)
        print("-------------- Stage 1 -------------")
        self.pass1()
        print("-------------- Stage 2 -------------")
        self.pass2()
        print("-------------- Results -------------")
        self.print_code()

    def pass1(self):
        """Starts the parsing of the file specified in the Reader class."""
        # TODO: Maybe update pass1 to capture variables/macros/labels?
        # Still have to possibly worry about global references that might
        # exist in other files or be references to an undefined label.
        self._line_no = 0
        nodes: List[CodeNode] = []
        # Pass 1 resolves symbols. Any global symbols are stored
        # in the Global symbols array.
        self.lexer.tokenize()
        for node in self.lexer.tokenized_list():
            nodes = self._np.process_node(node)
            if nodes:
                self.code.extend(nodes)

    def pass2(self):
        """
        Where pass1 resolves instructions as much as possible, for those
        references to labels that weren't properly resolved, pass2 will
        attempt to resolve the issues. This is done to code_nodes with a
        type of NODE which indicates that it is unprocessed likely
        because it contained a forward referenced label within the same
        file. Otherwise, it's possibly a global label or an error.
        """
        new_code: List[CodeNode] = []
        IP().base_address = 0x0000
        for (_, code_node) in enumerate(self.code):
            type_name = code_node.type_name
            code = code_node.code_obj
            if type_name == NODE:
                if not is_node_valid(code):
                    continue
                new_nodes = self._np.process_node(code)
                if new_nodes:
                    new_code.extend(new_nodes)
            else:
                IP().move_relative(code_node.offset)
                new_code.append(code_node)
        self.code.clear()
        self.code = new_code

    def print_code(self):
        """Print out the code"""
        pp = pprint.PrettyPrinter(indent=2, compact=False, width=40)
        for code_node in self.code:
            type_name = code_node.type_name
            type_name = type_name if type_name != INST else ""
            offset = code_node.offset
            code = code_node.code_obj
            if type_name == NODE:
                print("Invalid instruction:")
                pp.pprint(code)
                continue
            desc = f"Type: {type_name}\n"
            desc += f"{hex(IP().base_address + offset)}:   {code.__str__()}\n"
            # desc += f"Offset: {code_node.offset}\n"
            # desc += "Code:"
            # desc += pp.pformat(code.__str__())
            print(desc)

    # --==[ End of class ]==-- #
    # --------========[ End of class ]========-------- #


class Macro(object):
    """
    """
    def __init__(self, reader: FileReader):
        self.reader = reader

if __name__ == "__main__":
    asm = """
SECTION "CoolStuff",WRAM0
CLOUDS_X: DB $FF,$00,$FF,$00,$FF,$00,$FF,$00,$FF,$00,$FF,$00,$FF,$00,$FF,$00
BUILDINGS_X: DS 1
FLOOR_X: DS 1
PARALLAX_DELAY_TIMER: DS 1
FADE_IN_ACTIVE:: DS 1
FADE_STEP: DS 1
ALLOW_PARALLAX:: DS 1
READ_INPUT:: DS 1
START_PLAY:: DS 1

IMAGES    EQU $10
BIGVAL    EQU 65500

SECTION "game", ROMX

.update_game:
    ld HL, BIGVAL   ; should be 0x21 dc ff
    ld HL, SP+$55   ; should be 0xf8 55
    ldhl sp, $6a    ; should be 0xf8 6a
    ld A, (HL)
    jr nz, .update_game
    jr .continue_update_1
    ld A, (HL)
    XOR D
    CP H
    CP L
.continue_update_1:
    CP A
"""

    assembler = Assembler()
    assembler.load_from_buffer(asm)
    assembler.parse()

    #for item in _instructions:
    #    print(item)

    # print(f"Equates: {p.equates}")
    # print("--- BEGIN LABELS DUMP ---")
    # for item in Labels().items():
    #    print(item)
    # print("---- END LABELS DUMP ----")
