#
#
from typing import NewType
from enum import Enum, auto

class ParserException (Exception):
    """Base class of exceptions for the parser."""
    def __init__(self, message, line_text=None, line_number=None):
        filename = line_text if line_text is not None else "unk_file"
        lineno = line_number if line_number is not None else "unk_line"

        new_message = f"{message} [{filename}:{lineno}]"
        super().__init__(new_message)
        self.line_text = line_text
        self.line_number = line_number


class DefineDataError(ParserException):
    """An exception that occurs when a data define is invalid.
    These are errors that are thrown when processing the DS, DB,
    DW, or DL sections.
    """
    def __init__(self, message, line_text="", line_number=-1):
        super().__init__(message, line_text, line_number)


class SectionDeclarationError(ParserException):
    """An exception that is thrown if the SECTION definition is invalid."""
    def __init__(self, message, line_text="", line_number=-1):
        super().__init__(message, line_text, line_number)


class SectionTypeError(ParserException):
    """An exception that is thrown if the SECTION type (WRAM, etc.) is invalid."""
    def __init__(self, message, line_text="", line_number=-1):
        super().__init__(message, line_text, line_number)


class ErrorCode(Enum):
    """Instruction error codes."""
    INVALID_MNEMONIC = auto()
    INCOMPLETE_INSTRUCTION = auto()
    INVALID_OPERAND = auto()
    OPERAND_IS_NOT_NUMERIC = auto()
    MISSING_MACHINE_CODE = auto()
    INVALID_LABEL_NAME = auto()
    INVALID_LABEL_POSITION = auto()
    INVALID_REGISTER = auto()
    INVALID_REGISTER_POSITION = auto()
    INVALID_SECTION_POSITION = auto()
    INVALID_DECLARATION = auto()



####################################################################################################

class Error():
    """Represents an Error object used in Instruction related operations."""
    __messages = {
        ErrorCode.INVALID_MNEMONIC:
        "Error: Invalid mnemonic",

        ErrorCode.INCOMPLETE_INSTRUCTION:
        "Error: Incomplete instrution. One or more operands are missing",

        ErrorCode.INVALID_OPERAND:
        "Error: The operand provided is invalid",

        ErrorCode.MISSING_MACHINE_CODE:
        "Error: The resulting instruction did not produce any machine code",

        ErrorCode.INVALID_LABEL_NAME:
        "Error: The label name is not in a valid format.",

        ErrorCode.INVALID_LABEL_POSITION:
        "Error: The label name is not in a valid position.",

        ErrorCode.INVALID_REGISTER:
        "Error: The register is not a valid register",

        ErrorCode.INVALID_REGISTER_POSITION:
        "Error: The use of the register in this position is invalid",

        ErrorCode.OPERAND_IS_NOT_NUMERIC:
        "Error: The operand was not a valid numeric value",

        ErrorCode.INVALID_SECTION_POSITION:
        """Error: The SECTION declaration must be the first declaration in
        "the file.""",

        ErrorCode.INVALID_DECLARATION:
        """The declaration was not a know keyword or instruction or appears
        with invalid characters or spacing.
        """
    }

    def __init__(self, error_code: int, supplimental: str = "",
                 source_file: str = None, source_line: int = None):
        self._code = error_code
        self._supplimental = supplimental
        self._file = source_file
        self._line = source_line

    def __repr__(self):
        if self._code in Error.__messages:
            message = Error.__messages[self._code]
            if self._supplimental:
                message += ": [" + self._supplimental + "]"
            if self._file:
                line = str(self._line) if not None else "?"
                message += f"\nLocation: {self._file}:{line}\n"
        else:
            message = f"ERROR: Invalid error code: [{self._code}]"
        return message

    @property
    def code(self) -> int:
        """ Returns the error code passed when creating this Error object."""
        return self._code

    @property
    def supplimental(self) -> str:
        """ Returns the supplimental text passed when creating this Error
        object. """
        return self._supplimental

    @property
    def source_file(self) -> str:
        return self._file

    @property
    def source_line(self) -> int:
        return self._line
