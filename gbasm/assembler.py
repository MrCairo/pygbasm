"""
Z80 Assembler
"""
from enum import IntEnum, auto
from collections import namedtuple
import tempfile
import pprint
import gbasm_dev; gbasm_dev.set_gbasm_path()

from gbasm.reader import BufferReader, FileReader, Reader
from gbasm.section import Section
from gbasm.storage import Storage
from gbasm.exception import ParserException, Error, ErrorCode
from gbasm.equate import Equate
from gbasm.instruction import Instruction, InstructionPointer, InstructionSet
from gbasm.resolver import Resolver
from gbasm.label import Label, Labels
from gbasm.conversions import ExpressionConversion
from gbasm.basic_lexer import BasicLexer, is_multiple_node, is_node_valid
from gbasm.constants import NODE, DIR, TOK, EQU, LBL, INST, STOR, SEC

class CodeNode(namedtuple('CodeNode', 'type_name, code_obj')):
    pass


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

    def load_from_file(self, filename):
        """Loads the assembly program from a file."""
        self.filename = filename
        self.reader = FileReader(filename)

    def load_from_buffer(self, buffer_in):
        """Loads the assembly program from a memory buffer."""
        self.reader = BufferReader(buffer_in)

    def parse(self):
        """Starts the assembler's parser."""
        self._parser = Parser(self.reader)
        print("-------------- Stage 1 -------------")
        self._parser.stage1()
        print("-------------- Stage 2 -------------")
        self._parser.stage2()
        print("-------------- Results -------------")
        self._parser.print_code()

    # --==[ End of class ]==-- #
    # --------========[ End of class ]========-------- #


class Parser:
    """
    The main assembler parser class.
    """
    def __init__(self, reader: Reader):
        self._reader = reader
        self._tf = tempfile.TemporaryFile()
        self._line_no = 0
        self._lexer = BasicLexer(reader)
        self._code: [CodeNode] = []
        self._bad: [dict] = []
        self._sections: [Section] = []

    def __hash__(self):
        return self._tf.__hash__()

    def stage1(self):
        """Starts the parsing of the file specified in the Reader class."""
        self._line_no = 0
        nodes: [CodeNode] = []
        # Pass 1 resolves symbols. Any global symbols are stored
        # in the Global symbols array.
        self._lexer.tokenize()
        for node in self._lexer.tokenized_list():
            nodes = self._process_node(node)
            if nodes:
                self._code.extend(nodes)

    def stage2(self):
        """
        Performs stage 2 compile which is an attempt to resolve and nodes
        with a type of NODE which indicates that it is unprocessed likely
        because it contained a forward referenced label. If not, then it's
        a real error.
        """
        new_code: [CodeNode] = []
        for (_, code_node) in enumerate(self._code):
            type_name = code_node.type_name
            code = code_node.code_obj
            if type_name == NODE:
                if not is_node_valid(code):
                    continue
                new_nodes = self._process_node(code)
                if new_nodes:
                    new_code.extend(new_nodes)
            else:
                new_code.append(code_node)
        self._code.clear()
        self._code = new_code

    def print_code(self):
        """Print out the code"""
        pp = pprint.PrettyPrinter(indent=2, compact=False, width=40)
        for code_node in self._code:
            type_name = code_node.type_name
            code = code_node.code_obj
            if type_name == NODE:
                print("Invalid instruction:")
                pp.pprint(code)
                continue
            desc = f"\n\nType: {type_name}\n"
            desc += "Code:"
            desc += pp.pformat(code.__str__())
            print(desc)

    def _process_node(self, node: dict) -> [CodeNode]:
        nodes: [CodeNode] = []
        if not is_node_valid(node):
            self._bad.append(node)
            return None
        if node[DIR] == SEC:
            sec = self._process_section(node[TOK])
            if sec is None:
                msg = f"Error in parsing section directive. "\
                    "{self.filename}:{self._line_no}"
                err = Error(ErrorCode.INVALID_SECTION_POSITION,
                            supplimental=msg,
                            source_line=self._line_no)
                node["error"] = err
                nodes.append(CodeNode(NODE, node))
            else:
                nodes.append(CodeNode(SEC, sec))
            return nodes
        if is_multiple_node(node):
            # The MULTIPLE case is when a LABEL is on the same line as some
            # other data like an instruction. In some cases this is common
            # like an EQU that is supposed to contain both a LABEL and a
            # value or less common like a LABEL on the same line as an
            # INSTRUCTION.
            multi = self._process_multi_node(node)
            if not multi:
                nodes.append(CodeNode(NODE, node))
            else:
                nodes.extend(multi)
        # Just check for a label on it's own line.
        elif node[DIR] == LBL:
            label = self._process_label(node)
            Labels().add(label.code_obj)
            nodes.append(label)
        # Lastly, if not any of the above, it _might_be an instruction
        elif node[DIR] == INST:
            ins = self._process_instruction(node)
            if ins:
                nodes.append(ins)
            else:
                nodes.append(CodeNode(NODE, node))
        return nodes

    def _process_multi_node(self, node: dict) -> [CodeNode]:
        tok_list = node[TOK]
        nodes: [CodeNode] = []
        if len(tok_list) < 2:
            # err = Error(ErrorCode.INVALID_DECLARATION,
            #             source_line=self._line_no)
            return None
        # Record a label unless it's an equate. The equate object (which is
        # similar to a label) handles the storage of both.
        if tok_list[0][DIR] == LBL and tok_list[1][DIR] != EQU:
            clean = tok_list[0][TOK].strip("()")
            existing = Labels()[clean]
            if not existing:
                label = self._process_label(tok_list[0])
                Labels().add(label.code_obj)
            else:
                label = CodeNode(LBL, existing)
            nodes.append(label)
        # Equate has it's own required label. It's not a standard label
        # in that it can't start with a '.' or end with a ':'
        if tok_list[1][DIR] == EQU:
            equ = self._process_equate(node[TOK])
            nodes.append(equ)
        # An instruction is allowed to be on the same line as a label.
        elif tok_list[1][DIR] == INST:
            ins = self._process_instruction(tok_list[1])
            nodes.append(ins)
        # Storage values can be associated with a label. The label
        # then can be used almost like an EQU label.
        elif tok_list[1][DIR] == STOR:
            storage = self._process_storage(tok_list[1])
            if storage:
                IP().move_location_relative(len(storage.code_obj))
                nodes.append(storage)
                return nodes
        else:
            nodes.append(CodeNode(NODE, node))
        return nodes

    def _process_instruction(self, node: dict) -> CodeNode:
        """
        Processes the instruction defined in the tokenized node.
        """
        address = None
        ins = None
        if node is None:
            return None
        ins = Instruction(node)
        if ins.parse_result().is_valid():
            IP().move_relative(len(ins.machine_code()))
            return CodeNode(INST, ins)
        # Instruction is not valid. This could mean either it really is
        # invalid (typo, wrong argument, etc) or that it has a label. To
        # get started, just check to make sure the mnemonic is at least
        # valid.
        if ins.parse_result().mnemonic_error() is None:
            ins2 = Resolver().resolve_instruction(ins, IP().location)
            if ins2 and ins2.is_valid():
                IP().move_relative(len(ins2.machine_code()))
                return CodeNode(INST, ins2)
        if ins and ins.is_valid():
            if address is not None:
                ins.address = address
            IP().move_relative(len(ins.machine_code()))
            return CodeNode(INST, ins)
        return CodeNode(NODE, node)  # Error, return the errant node

    def _process_label(self, node: dict, value=None) -> CodeNode:
        if not node:
            return None
        if node[DIR] != LBL:
            return None
        clean = node[TOK].strip("()")
        existing = Labels()[clean]
        if existing:
            return None
        loc = value
        if not value:
            loc = IP().location
        label = Label(clean, loc)
        return CodeNode(LBL, label)

    def _process_equate(self, tokens: list) -> CodeNode:
        """Process an EQU statement. """
        # The tokens should always be multiple since an EQU contains
        # a label followed by the EQU to associate with the label
        if len(tokens) < 2:
            return None
        if tokens[0][DIR] != 'LABEL':
            return None
        if tokens[1][DIR] != 'EQU':
            return None
        result = Equate(tokens)
        if result:
            result.parse()
            lbl = Label(result.name(), result.value(), force_const=True)
            Labels().add(lbl)
            return CodeNode(EQU, lbl)
        err = Error(ErrorCode.INVALID_LABEL_NAME,
                    source_file=self._reader.filename,
                    source_line=int(self._reader.line))
        tokens["error"] = err
        # _errors.append(err)
        return CodeNode(NODE, tokens)

    def _process_storage(self, node: dict) -> CodeNode:
        if not node:
            return None
        sto = Storage(node)
        # print(f"Processing Storage type {sto.storage_type()}")
        # print(f"Storage len = {len(sto)}")
        return CodeNode(STOR, sto)

    def _find_section(self, line: str) -> Section:
        try:
            section = Section(line)
        except ParserException:
            fname = self._reader.filename()
            msg = f"Parser exception occured {fname}:{self._line_no}"
            print(msg)
            raise ParserException(msg, line_number=self._line_no)
        else:
            if section:
                for _, val in enumerate(self._sections):
                    if val.name() == section.name():
                        return section
            return None

    def _process_section(self, tokens: dict) -> Section:
        if not tokens or (tokens and tokens[0] != SEC):
            return None
        if len(tokens) < 3:
            return None
        try:
            section = self._find_section(' '.join(tokens))
        except ParserException:
            return None
        if section is None:  # not found, create a new one.
            secn = Section(tokens)
            # print("Processing SECTION")
            self._sections.append(secn)
            num_addr, _ = secn.address_range()
            str_addr = EC().expression_from_value(num_addr,
                                                  "$$")  # 16-bit hex value
            IP().base_address = str_addr

            return secn

        return None

    # --- End of class
    

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
