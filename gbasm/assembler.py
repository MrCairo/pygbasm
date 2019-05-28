"""
Z80 Assembler
"""
from enum import IntEnum, auto
from collections import namedtuple
import tempfile

from gbasm.reader import BufferReader, FileReader, Reader
from gbasm.section import Section
from gbasm.storage import Storage
from gbasm.exception import ParserException, Error, ErrorCode
from gbasm.equate import Equate
from gbasm.instruction import Instruction, InstructionPointer, InstructionSet
from gbasm.resolver import Resolver
from gbasm.label import Label, Labels, is_valid_label
from gbasm.conversions import ExpressionConversion
from gbasm.basic_lexer import BasicLexer, is_multiple_node, is_node_valid
from gbasm.constants import NODE, DIR, TOK, EQU, LBL, INST, STOR, SEC

class CodeNode(namedtuple('CodeNode', 'type_name, code_obj')):
    pass

_errors: [Error] = []
_sections: [Section] = []

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
        self._buffer = None
        self.reader = None
        self.line_no = 0
        self.errors = []
        self.warnings = []
        self._assemble: [dict] = []
        self._parser = None

    def load_from_file(self, filename):
        """Loads the assembly program from a file."""
        self.filename = filename
        self.reader = FileReader(filename)

    def load_from_buffer(self, buffer_in):
        """Loads the assembly program from a memory buffer."""
        self._buffer = buffer_in
        self.reader = BufferReader(self._buffer)

    def parse(self):
        """Starts the assembler's parser."""
        self._parser = Parser(self.reader)
        print("-------------- Stage 1 -------------")
        self._parser.stage1()
        print("-------------- Stage 2 -------------")
        self._parser.stage2()
        # self._parser.resolve_bad()

    def add_assembled(self, directive: str, assembled_object):
        self._assemble.append({DIR: directive,
                               "OBJ": assembled_object})

    # --------========[ End of class ]========-------- #

class Parser:
    """
    The main assembler parser class.
    """
    def __init__(self, reader: Reader):
        self._reader = reader
        self._state = ParserState.IDLE
        self._action = Action.INITIAL
        self._tf = tempfile.TemporaryFile()
        self._fileline = ""
        self._line_no = 0
        self._lexer = BasicLexer(reader)
        self._code: [CodeNode] = []
        self._bad: [dict] = []

    def __hash__(self):
        return self._tf.__hash__()

    def stage1(self):
        """Starts the parsing of the file specified in the Reader class."""
        self._line_no = 0
        nodes: [CodeNode] = []
        start_file_pos = self._reader.get_position()

        # Pass 1 resolves symbols. Any global symbols are stored
        # in the Global symbols array.
        self._state = ParserState.RESOLVE
        self._action = Action.UNDETERMINED
        self._lexer.tokenize()
        for node in self._lexer.tokenized_list():
            nodes = self.process_node(node)
            if nodes:
                self._code.extend(nodes)

    def stage2(self):
        """
        """
        for (_, node) in enumerate(self._code):
            type_name = node.type_name
            code = node.code_obj
            print(f"\nType name: {type_name}")
            print(f"Code: {code}")
    #
    # Pre-process step. Symbol/SECTION/EQU processing.
    #
    def preprocess(self) -> None:
        """
        Preprocesses the line in the file. A return value of None
        indicates a success, otherwise an Error object is returned.
        """
        nodes: [CodeNode] = []
        for node in self._lexer.tokenized_list():
            if not is_node_valid(node):
                self._bad.append(node)
                continue
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
                continue

            # The MULTIPLE case is when a LABEL is on the same line as some
            # other data like an instruction. In some cases this is common
            # like an EQU that is supposed to contain both a LABEL and a
            # value or less common like a LABEL on the same line as an
            # INSTRUCTION.
            if is_multiple_node(node):
                if not self._process_multi_node(node):
                    continue
            # Just check for a label on it's own line.
            if node[DIR] == LBL:
                label = self._process_label(node)
                Labels().add(label)
                self._code.append(CodeNode(LBL, label))
            # Lastly, if not any of the above, it _might_be an instruction
            elif node[DIR] == INST:
                ins = self._process_instruction(node)
                if ins:
                    self._code.append(CodeNode(INST, ins))
                else:
                    self._code.append(CodeNode(NODE, node))


    def process_node(self, node: dict) -> [CodeNode]:
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

        # The MULTIPLE case is when a LABEL is on the same line as some
        # other data like an instruction. In some cases this is common
        # like an EQU that is supposed to contain both a LABEL and a
        # value or less common like a LABEL on the same line as an
        # INSTRUCTION.
        if is_multiple_node(node):
            multi = self._process_multi_node(node)
            if not multi:
                nodes.append(CodeNode(NODE, node))
            else:
                nodes.extend(multi)
        # Just check for a label on it's own line.
        if node[DIR] == LBL:
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

    def resolve_bad(self):
        """
        """
        for (idx, node) in enumerate(self._bad):
            if not is_node_valid(node):
                continue
            ins = None
            if node[DIR] == INST:
                ins = Instruction(node)
            else:
                print(f"Node isn't an Inst: {node}")
                continue
            if ins.is_valid():
                continue
            if ins.parse_result().mnemonic_error() is None:
                ins = Resolver().resolve_instruction(ins, IP().location)
                print(ins)

    def _assemble(self, line: str):
        clean: str = line.upper().strip()
        print(f">>> Processing: {line}")
        self._action = Action.UNDETERMINED

        if not clean:
            return

        if clean.startswith(SEC):
            section = self._find_section(line)
            if section:
                self._action = Action.SECTION

        elif " EQU " in clean:
            self._action = Action.EQU

        elif clean[:3] in ["DS ", "DB ", "DW ", "DL "]:
            print(f"Processing {clean[:2]} Line {self._line_no}")
            self._action = Action.STORAGE
            if self._process_storage(clean[3:]) is False:
                msg = f"Error on line {self._fileline} \n>> {clean}"
                raise ParserException(msg, line_number=self._line_no)
        elif line[0] in Labels().first_chars:
            """
            All the work to process labels was done in the pre-process
            step.  Now, if there is an instruction after the label, we
            need to process it.
            """
            words = clean.split(":")
            if len(words) > 1:
                clean = words[1].strip()  # Maybe code?
                self._action = Action.UNDETERMINED
            else:
                self._action = Action.IGNORE

        if not clean:
            return  # Leave if there is nothing else to parse.

        # UNDETERMINED means that it's likely an instruction.
        # CODE means that it's NOT an EQU or SECTION or if a LABEL was
        # processed.
        if self._action == Action.UNDETERMINED:
            ins = self._process_instruction(clean)
            if ins is None:
                print(f"UNABLE TO PARSE INSTRUCTION [{clean}]")
            else:
                print(ins)
        return

    @staticmethod
    def _label_def_in_string(line: str) -> str:
        # Validate column0. Must not be a space or
        col0 = None if not line else line[0]
        if col0 is not None:
            col0 = None if col0 not in Labels.valid_chars else col0

        if col0 is None:
            return None

        parts = line.split(" ")
        return parts[0]

    def _process_multi_node(self, node: dict) -> [CodeNode]:
        tok_list = node[TOK]
        nodes: [CodeNode] = []
        if len(tok_list) < 2:
            err = Error(ErrorCode.INVALID_DECLARATION,
                        source_line=self._line_no)
            _errors.append(err)
            return None
        if tok_list[0][DIR] == LBL:
            label = self._process_label(tok_list[0])
            nodes.append(label)
            Labels().add(label.code_obj)
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
        # Make sure the mnemonic is at least valid.
        if ins.parse_result().mnemonic_error() is None:
            ins = Resolver().resolve_instruction(ins, IP().location)
            if ins and ins.is_valid():
                IP().move_relative(len(ins.machine_code()))
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
        print(f"Processing Storage type {sto.storage_type()}")
        print(f"Storage len = {len(sto)}")
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
                for _, val in enumerate(_sections):
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
            print("Processing SECTION")
            _sections.append(secn)
            num_addr, _ = secn.address_range()
            str_addr = EC().expression_from_value(num_addr,
                                                  "$$")  # 16-bit hex value
            IP().base_address = str_addr

            return secn
        return None

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

        clean_split = clean.split()
        tokens = {}
        line = Parser._join_parens(line)
        if clean.startswith(SEC):
            tokens[DIR] = SEC
            line = line.replace(',', ' ')
            tokens[TOK] = clean.split()
            return tokens
        if clean.startswith("EQU "):
            clean = clean.strip()
            tokens[DIR] = "EQU"
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
        if line[0] in Labels().first_chars:
            if is_valid_label(clean_split[0]):
                data = [{"type": LBL,
                         "data": clean_split[0]}]
                tokens[DIR] = "MULTIPLE"
                if len(clean_split) > 1:
                    remainder = ' '.join(clean_split[1:])
                    more = Parser._tokenize_line(remainder)
                    data.append(more)
                tokens[TOK] = data
                return tokens
        tokens[DIR] = "UNKNOWN"
        tokens[TOK] = clean.split()
        return tokens

class Macro(object):
    """
    """
    def __init__(self, reader: FileReader):
        self.reader = reader


def _substitute_label(line: str, label: Label, placeholder: str = None) -> str:
    output = ""
    line = "" if line is None else line
    components = line.split(" ")
    for item in components:
        result = item
        if label.clean_name in item:
            val = EC().expression_from_value(label.value, "$")
            if val:
                result = item.replace(label.clean_name, val)
        if result:
            output += result + " "
    return output.strip()


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
BIGVAL    EQU $C020

SECTION "game", ROMX

.update_game:   ld HL, BIGVAL
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
    print("--- BEGIN LABELS DUMP ---")
    for item in Labels().items():
        print(item)
    print("---- END LABELS DUMP ----")
