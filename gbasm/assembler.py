"""
Z80 Assembler
"""
import string
from enum import IntEnum, auto
from gbasm.reader import BufferReader, FileReader, Reader
from gbasm.section import Section
from gbasm.exception import ParserException, Error, ErrorCode
from gbasm.equate import Equate
from gbasm.instruction import *
from gbasm.label import Label, Labels
from gbasm.conversions import ExpressionConversion
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

    def __init__(self, reader: Reader, assembler):
        self._reader = reader
        self._state = ParserState.IDLE
        self._action = Action.INITIAL
        self._tf = tempfile.TemporaryFile()
        self._fileline = ""

        def __hash__(self):
            return self._tf.__hash__()

    def parse(self):
        self.line_no = 0
        self._equate_parser = Equate(self._reader)
        start_file_pos = self._reader.get_position()

        # Pass 1 resolves symbols. Any global symbols are stored
        # in the Global symbols array.
        self._state = ParserState.RESOLVE
        self._action = Action.UNDETERMINED
        while self._reader.is_eof() is False:
            line = self._reader.read_line()
            if line:
                line = line.upper().split(";")[0]  # drop comments
                self.line_no += 1
                self._fileline = f"{self._reader.filename()}:{self.line_no}"
                result = self._preprocess(line)

        self.line_no = 0
        self._state = ParserState.ASSEMBLE
        self._reader.set_position(start_file_pos)
        while self._reader.is_eof() is False:
            line = self._reader.read_line()
            if line and line.strip():
                line = line.upper().split(";")[0]  # drop comments
                self.line_no += 1
                self._fileline = f"{self._reader.filename()}:{self.line_no}"
                self._assemble(line)

    #
    # Pre-process step. Symbol/SECTION/EQU processing.
    #
    def _preprocess(self, line):
        """Preprocesses the line in the file. A return value of None
        indicates a success, otherwise an Error object is returned."""

        clean = line.strip()
        if not clean:
            return None  # Empy line

        if clean.startswith("SECTION"):
            if not self._process_section(line):
                msg = f"Error in parsing section directive. "\
                    "{self.filename}:{self.line_no}"
                return Error(ErrorCode.INVALID_SECTION_POSITION,
                             source_line=self.line_no)
            self._action = Action.SECTION
        elif " EQU " in clean:
            if self._action != Action.SECTION and self._action != Action.EQU:
                raise ParserException("EQU before Section",
                                      line_number=self.line_no)
            self._action = Action.EQU
            _ = self._process_equate(clean)
        elif line[0] in Labels.first_chars:
            """
            Test if the label is before a SECTION is defined.
            """
            if not self.sections:
                msg = "A label cannot appear before a SECTION."
                return Error(ErrorCode.INVALID_LABEL_POSITION,
                             supplimental=msg,
                             source_line=self.line_no)
            words = line.split()
            if words[0].endswith(":") and words[0].startswith("."):
                self._action = Action.CODE
                label = Label(words[0], InstructionPointer().location)
                label.constant = False
                Labels()[words[0]] = label
        return None

    def _assemble(self, line: str):
        clean: str = line.upper().strip()
        self._action = Action.UNDETERMINED

        if not clean:
            return

        if clean.startswith("SECTION"):
            self._action = Action.SECTION

        elif " EQU " in clean:
            self._action = Action.EQU

        elif clean[:3] in ["DS ", "DB ", "DW ", "DL "]:
            print(f"Processing {clean[:2]} Line {self.line_no}")
            self._action = Action.STORAGE
            if self._process_storage(clean[3:]) is False:
                msg = f"Error on line {fileline} \n>> {clean}"
                raise ParserException(msg, line_number=self.line_no)
        elif line[0] in Labels.first_chars:
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
            instruction = self._process_instruction(clean)
            if instruction is None:
                print(f"UNABLE TO PARSE INSTRUCTION [{clean}]")
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
            if ins.parse_result.:
                ph = ins.parse_result.placeholder
                supp = ins.parse_result.error.supplimental
                possible_label = supp.strip("(.:)")
                label: Label = Labels()[possible_label]
                if label:
                    line = _substitute_label(line, label, ph.placeholder)
                    ins = Instruction(line)
                else:
                    ins = None
        if not ins:
            ins = Instruction(line)
        print(ins.instruction)
        if ins.is_valid():
            if address is not None:
                ins.address = address
            self.instructions.append(ins)
            InstructionPointer().move_relative(len(ins.machine_code))
            print(ins)
        else:
            # Check for and process a label.
            # If None is returned, it's an invalid instruction.
            ins = self._process_label(line)
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

    def _process_section(self, line):
        try:
            section = Section(self._reader)
        except ParserException:
            msg = f"Parser exception occured {self.filename}:{self.line_no}"
            print(msg)
            raise ParserException(msg, line_number=self.line_no)
        else:
            if section:
                print(f"\n{section}\n")
                self.sections.append(section)
                num_addr, _ = section.address_range
                str_addr = EC.expression_from_value(num_addr,
                                                    "$$")  # 16-bit hex value
                InstructionPointer().base_address = str_addr
                print(f"IP = {InstructionPointer().location}\n")
                return True
            return False

    def _process_equate(self, line) -> Label:
        """Process an EQU statement. """
        result = Equate(line).parse()
        if 'label' in result and 'value' in result:
            label = Label(result['label'], int(result['value']))
            label.is_constant = True
            Labels().add(label)
            return label
        err = Error(ErrorCode.INVALID_LABEL_NAME,
                    source_file=self._reader.filename,
                    source_line=int(self._reader.line))
        self.errors.append(err)
        return None

    def _process_storage(self, line):
        print("Storage")



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
            val = EC.expression_from_value(label.value, "$")
            if val:
                result = item.replace(label.clean_name, val)
        if result:
            output += result + " "
    return output.strip()


if __name__ == "__main__":
    asm = """
SECTION "NewSection", WRAM0[$C100]

IMAGES    EQU $10
BIGVAL    EQU $C020

.program_start:
    ld B, $16 ; This is a comment
    ld BC, $FFD2
    ld a, IMAGES
    LD (BC), A

    JR .program_start
    LD (BIGVAL), A
    ret
    """

    parser = Parser()
    parser.load_from_buffer(asm)
    parser.parse()

    # print(f"Equates: {p.equates}")
    # print("--- BEGIN LABELS DUMP ---")
    # print(Labels().items())
    # print("---- END LABELS DUMP ----")
