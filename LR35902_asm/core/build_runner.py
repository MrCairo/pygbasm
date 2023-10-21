"""
Global storage for the Game Boy Assembler.

The idea behind the BuildRunner class is to design can keep track of the
compilation process as far as addresses are concerned. This means:
    * keeping track of the IP from a compilation perspective
    * Assignment of addresses to labels
    * Obeying the rules of the SECTION (ORG) class
    * Keeping the InstructionPointer class up-to-date
    * Storing local and global labels.
"""

from dataclasses import dataclass
from singleton_decorator import singleton
from .symbol import Symbol, SymbolScope, Symbols
from .instruction_pointer import InstructionPointer
from .section import Section


@dataclass
class BuildRunnerData:
    insPtr: InstructionPointer = None
    currSec: Section = None
    currMajorSymbol: Symbol = None
    currMinorSymbol: Symbol = None


@singleton
class BuildRunner:

    def __init__(self):
        """Initialize the object."""
        self._symbols = Symbols()
        self._running_data = BuildRunnerData()

    @property
    def instruction_pointer(self) -> InstructionPointer:
        """Return the current IP based upon the state of this class."""
        return self._running_data.insPtr

    @instruction_pointer.setter
    def instruction_pointer(self, new_value: int):
        if self._running_data.insPtr is None:
            self._instructionPointer = InstructionPointer()
        self._running_data.insPtr.location = new_value

    @property
    def curr_section(self) -> Section:
        """Return the current SECTION attributes in effect."""
        return self._running_data.curr_section

    @curr_section.setter
    def curr_section(self, new_value: Section):
        self._running_data.currSec = new_value

    @property
    def curr_major_symbol(self) -> Symbol:
        return self._running_data.currMajorSymbol

    @curr_major_symbol.setter
    def curr_major_symbol(self, new_value: Symbol):
        if new_value.scope in [SymbolScope.LOCAL, SymbolScope.GLOBAL]:
            self._running_data.currMajorSymbol = new_value
        else:
            raise ValueError(new_value)

    @property
    def curr_minor_symbol(self) -> Symbol:
        return self._running_data.currMinorSymbol

    @curr_minor_symbol.setter
    def curr_minor_symbol(self, new_value: Symbol):
        if new_value.scope == SymbolScope.PRIVATE:
            self._running_data.currMinorSymbol
        else:
            raise ValueError(new_value)
