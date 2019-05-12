"""
Z80 Assembler
"""
import string
from enum import IntEnum, auto
import pprint
from gbasm.reader import BufferReader, FileReader, Reader
from gbasm.section import Section
from gbasm.exception import ParserException, Error, ErrorCode
from gbasm.equate import Equate
from gbasm.instruction import Instruction, InstructionPointer
from gbasm.instruction import InstructionSet
from gbasm.resolver import Resolver
from gbasm.label import Label, Labels, is_valid_label
from gbasm.conversions import ExpressionConversion
from gbasm.basic_lexer import BasicLexer
import tempfile

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

_instructions: [Instruction] = []
_clean_lines: list = []
_errors: list = []
_sections: list = []
_storage: list = []
_tokenized: list = []

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

    def load_from_file(self, filename):
        self.filename = filename
        self.reader = FileReader(filename)

    def load_from_buffer(self, buffer_in):
        self._buffer = buffer_in
        self.reader = BufferReader(self._buffer)

    def parse(self):
        parser = Parser(self.reader)
        parser.parse()


class Parser:
    _lexer: BasicLexer
    _line_no = 0
    _reader: Reader
    _fileline = ""

    def __init__(self, reader: Reader):
        self._reader = reader
        self._state = ParserState.IDLE
        self._action = Action.INITIAL
        self._tf = tempfile.TemporaryFile()
        self._fileline = ""
        self._line_no = 0
        self._lexer = BasicLexer(reader)

        def __hash__(self):
            return self._tf.__hash__()

    def parse(self):
        self._line_no = 0
        start_file_pos = self._reader.get_position()

        # Pass 1 resolves symbols. Any global symbols are stored
        # in the Global symbols array.
        self._state = ParserState.RESOLVE
        self._action = Action.UNDETERMINED
        self._lexer.tokenize()
        p = pprint.PrettyPrinter(indent=4)
        p.pprint(self._lexer.tokenized_list())

        return
        self._line_no = 0
        self._state = ParserState.ASSEMBLE
        self._reader.set_position(start_file_pos)
        while self._reader.is_eof() is False:
            line = self._reader.read_line()
            if line and line.strip():
                line = line.upper().split(";")[0]  # drop comments
                self._line_no += 1
                self._fileline = f"{self._reader.filename()}:{self._line_no}"
                self._assemble(line)

    #
    # Pre-process step. Symbol/SECTION/EQU processing.
    #
    def _preprocess(self, line) -> None:
        """Preprocesses the line in the file. A return value of None
        indicates a success, otherwise an Error object is returned."""

        clean = line.strip()
        if not clean:
            return None  # Empy line

        if clean.startswith("SECTION"):
            if self._process_section(line) is None:
                msg = f"Error in parsing section directive. "\
                    "{self.filename}:{self._line_no}"
                err = Error(ErrorCode.INVALID_SECTION_POSITION,
                            source_line=self._line_no)
                _errors.append(err)
                return
            self._action = Action.SECTION
            _clean_lines.append(clean)
        elif " EQU " in clean:
            if self._action != Action.SECTION and self._action != Action.EQU:
                raise ParserException("EQU before Section",
                                      line_number=self._line_no)
            self._action = Action.EQU
            _ = self._process_equate(clean)
            _clean_lines.append(clean)
        elif line[0] in Labels().first_chars:
            """
            Test if the label is before a SECTION is defined.
            """
            if not len(_sections):
                msg = "A label cannot appear before a SECTION."
                err = Error(ErrorCode.INVALID_LABEL_POSITION,
                            supplimental=msg,
                            source_line=self._line_no)
                _errors.append(err)
                return
            words = line.split()
            if words[0].endswith(":") and words[0].startswith("."):
                label_str = words[0]
                ins_str = ""
                if len(words) > 1:
                    self._action = Action.CODE
                    for i in range(1, len(words)):
                        ins_str += words[i] + " "
                label = Label(words[0], InstructionPointer().location)
                label.constant = False
                Labels()[words[0]] = label
                _clean_lines.append(label_str)
                if len(ins_str):
                    _clean_lines.append(ins_str)
        elif line[0] == ' ':
            exploded = line.strip().split()
            if IS().is_mnemonic(exploded[0]):
                _clean_lines.append(clean)

        return

    def _assemble(self, line: str):
        clean: str = line.upper().strip()
        print(f">>> Processing: {line}")
        self._action = Action.UNDETERMINED

        if not clean:
            return

        if clean.startswith("SECTION"):
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

    def label_def_in_string(self, line: str) -> str:
        # Validate column0. Must not be a space or
        col0 = None if not line else line[0]
        if col0 is not None:
            col0 = None if col0 not in Labels.valid_chars else col0

        if col0 is None:
            return None

        parts = line.split(" ")
        return parts[0]

    def _process_instruction(self, line: str):
        address = None
        ins = None
        if line is not None:
            ins = Instruction(line)
            if ins.parse_result().is_valid():
                print("--- Resolved:")
                IP().move_relative(len(ins.machine_code()))
                return ins
            # Make sure the mnemonic is at least valid.
            if ins.parse_result().mnemonic_error() is None:
                ins = Resolver().resolve_instruction(ins, IP().location)
                if ins and ins.is_valid():
                    IP().move_relative(len(ins.machine_code()))
                    print("--- Resolved with label:")
#            ins = self._process_label(line)
        if ins and ins.is_valid():
            if address is not None:
                ins.address = address
            _instructions.append(ins)
            IP().move_relative(len(ins.machine_code()))
        else:
            print(f"ERROR: {line}")
        return ins

    def _process_label(self, line):
        clean = line.strip("(.:)")
        ins = None
        existing: Label = Labels()[clean]
        if existing:
            print(f"Found label: {existing}")
            new_line = line.replace(clean, str(existing.offset()))
            ins = Instruction(new_line)
            if ins and line.startswith("."):
                ins.address = existing.offset
        return ins


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

    def _process_section(self, line) -> Section:
        try:
            section = self._find_section(line)
        except ParserException as parse_exception:
            raise parse_exception
        if section is None:
            section = Section(line)
            _sections.append(section)
            num_addr, _ = section.address_range()
            str_addr = EC().expression_from_value(num_addr,
                                                  "$$")  # 16-bit hex value
            InstructionPointer().base_address = str_addr
            print(f"IP = {InstructionPointer().location}\n")
            return section
        return None

    def _process_equate(self, line) -> Label:
        """Process an EQU statement. """
        result = Equate(line).parse()
        if result:
            result.is_constant = True
            Labels().add(result)
            return result
        err = Error(ErrorCode.INVALID_LABEL_NAME,
                    source_file=self._reader.filename,
                    source_line=int(self._reader.line))
        _errors.append(err)
        return None

    def _process_storage(self, line):
        print("Storage")

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
        if clean.startswith("SECTION"):
            tokens['directive'] = "SECTION"
            line = line.replace(',', ' ')
            tokens['tokens'] = clean.split()
            return tokens
        if clean.startswith("EQU "):
            clean = clean.strip()
            tokens['directive'] = "EQU"
            tokens['tokens'] = clean_split
            return tokens
        if clean_split[0] in ["DS", "DB", "DW", "DL"]:
            tokens['directive'] = "STORAGE"
            tokens['tokens'] = clean_split
            return tokens
        if IS().is_mnemonic(clean_split[0]):
            tokens['directive'] = 'INSTRUCTION'
            tokens['tokens'] = clean_split
            return tokens
        if line[0] in Labels().first_chars:
            if is_valid_label(clean_split[0]):
                data = [{"type": "LABEL",
                         "data": clean_split[0]}]
                tokens['directive'] = "MULTIPLE"
                if len(clean_split) > 1:
                    remainder = ' '.join(clean_split[1:])
                    more = Parser._tokenize_line(remainder)
                    data.append(more)
                tokens['tokens'] = data
                return tokens
        tokens['directive'] = "UNKNOWN"
        tokens['tokens'] = clean.split()
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
SECTION "NewSection", WRAM0
CLOUDS_X: DS 1
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
	cp $00
	jr nz, .update_game
	jr .continue_update_1
	ld A, (HL)
	cp $00
	XOR D
.continue_update_1:
	CP H
	CP L
	CP A
"""

    assembler = Assembler()
    assembler.load_from_buffer(asm)
    assembler.parse()

    # print(f"Equates: {p.equates}")
    # print("--- BEGIN LABELS DUMP ---")
    # print(Labels().items())
    # print("---- END LABELS DUMP ----")
