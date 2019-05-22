"""
Implementation of a Section
"""
#
# Class that parses and contains information about a section.
# There can only be one section per file.
#
import string
from collections import namedtuple
from gbasm.exception import SectionDeclarationError, SectionTypeError
from gbasm.basic_lexer import BasicLexer
from gbasm.constants import EQU, LBL, INST, STOR

###############################################################################

# Class that is just a namedtuple representing the Section start and end
# address.
class SectionAddress(namedtuple('SectionAddress', 'start, end')):
    pass


###############################################################################

class SectionType:

    def __init__(self):
        #                                             start, end
        #-------------------------------------------------------------
        self._sections = {"WRAM0": {'id': 0, 'addr':(0xC000, 0xCFFF)},
                          "VRAM":  {'id': 1, 'addr':(0x8000, 0x9FFF)},
                          "ROMX":  {'id': 2, 'addr':(0x4000, 0x7FFF)},
                          "ROM0":  {'id': 3, 'addr':(0x0000, 0x3FFF)},
                          "HRAM":  {'id': 4, 'addr':(0xFF80, 0xFFFE)},
                          "WRAMX": {'id': 5, 'addr':(0xD000, 0xDFFF)},
                          "SRAM":  {'id': 6, 'addr':(0xA000, 0xBFFF)},
                          "OAM":   {'id': 7, 'addr':(0xFE00, 0xFE9F)}}


    @property
    def sections(self):
        return self._sections


    def is_valid_sectiontype(self, sectionType):
        sec = sectionType.upper().strip()
        valid = (sec in self.sections.keys())
        if not valid:
            valid = (sec in ["BANK", "ALIGN"])
        return valid

    def sectiontype_info(self, sectiontype):
        if sectiontype in self._sections:
            return self._sections[sectiontype]
        else:
            return None


###############################################################################
class Section:
    """
    Handles the parsing of a SECTION line.
    The return value of the "parseLine" is a dictionary
    """
    _types = [EQU, LBL, INST, STOR]

    #
    # Init with the reader object. The line in the reader (or the one to be read)
    # must be the line with the SECTION keyword. If not, this class will be
    # considered invalid.
    #
    def __init__(self, tokens: dict):
        self._sec_name = ""
        self._tokens = tokens
        self._parser = SectionParser(tokens)
        self._parsed = self._parser.parsed_data()
        self._storage = []

    def __str__(self):
        if self.is_valid:
            start, end = self.address_range()
            desc = f"Section Name  '{self.name()}'\n" \
                   f"Address Range '{start:04X} - {end:04X}'\n"
            return desc
        return "None"

    def __repr__(self):
        desc = f"Section({self._tokens})"
        return desc

    @staticmethod
    def typename():
        """Returns the string name of this class's type."""
        return "Section"

    @classmethod
    def from_string(cls, text: str):
        "Initialize Section from a string"
        tok = BasicLexer.from_text(text)
        tok.tokenize()
        tok_list = tok.tokenized_list()
        if len(tok_list):
            if tok_list[0]['directive'] == "SECTION":
                return cls(tok_list[0]['tokens'])
        return cls({})

    def name(self) -> str:
        """Returns the name of this section."""
        return self._parsed['name'] if self.is_valid() else None

    def address_range(self) -> SectionAddress:
        """Returns the address range in a SectionAddress object."""
        return self._parsed['address_range'] if self.is_valid() else None

    def args(self) -> dict:
        """Returns a dictionary of args of the section declaration."""
        return self._parsed['args'] if self.is_valid() else None

    def is_valid(self) -> bool:
        """Returns True if this Section object is valid."""
        return self._parsed and \
            self._parsed['name'] and \
            self._parsed['address_range']

    def append(self, type_str: str, value) -> bool:
        """
        Adds objects included in this section.
        """
        if type_str not in self._types:
            return False
        data = {"type": type_str,
                "object": value}
        self._storage.append(data)
        return True

    # --------========[ End of class ]========-------- #

class SectionParser:
    """Parses a possible SECTION line """
    _data: dict
    _tokens: dict
    _sec_type: SectionType

    def __init__(self, tokens: dict):
        self._tokens = tokens
        self._sec_type = SectionType()
        try:
            self._data = self._parse_line()
        except SectionDeclarationError as sde:
            print(sde)
            self._data = None

    def parsed_data(self):
        """Returns the parsed_data dictionary"""
        return self._data

    def section_type(self) -> SectionType:
        """Returns the section type (i.e WRAM0)"""
        return self._sec_type

    def is_section(self):
        if len(self._tokens) < 3:
            return False
        if self._tokens[0].upper() != "SECTION":
            return False
        return True

    # -----=====< End of public section >=====----- #

    def _parse_line(self) -> dict:
        if not self.is_section():
            return None
        parsed = self._validate()
        if parsed:
            self._parsed = parsed
        return parsed

    def _validate(self) -> dict:
        """
        SECTION "SectionNameInQuotes", ROMX[$4000],BANK[3]
        """
        # { 'section':'name', 'args':{'symbol':'ROMX', 'param':'$4000',...} }
        result = None

        #
        # Input should look like:
        # SECTION "SectionNameInQuotes",SECTION_TYPE[$4000]
        #
        if self.is_section():
            result = {}
            sec = self._get_section_and_name()
            # There should be at least 2 elements. Any less represents an error

            if sec is None:
                raise SectionDeclarationError("Invalid Section format.",
                                              line_text=line)
            # ['"sectionName"', "ROMX", "BANK[3]"]
            result['name'] = sec['name']
            # Get the symbols. There needs to be at least one.
            symbols = []  # An array of Dictionaries: { 'symbol':'ROMX',
                          #                             'param':'$4000'}
            args = self._tokens[2:]
            for (idx, _) in enumerate(args):
                sym_dict = {"symbol":'', 'param':''}
                sym = args[idx].split('[')
                if not self._sec_type.is_valid_sectiontype(sym[0]):
                    raise SectionTypeError(f"The section type '{sym[0]}' "\
                                           "is not a valid section type.")
                sym_dict["symbol"] = sym[0]
                if len(sym) > 1: # Will be something line "$4000]"
                    sym_dict['param'] = sym[1].strip("]")
                symbols.append(sym_dict)
            result['args'] = symbols
            result['address_range'] = self._compute_address(symbols)
        return result

    def _get_section_and_name(self):
        """Tokens 0 should be SECTION and tokens[1] == the name"""
        result = {}

        name = self._tokens[1].strip().strip("\"'")
        valid = string.ascii_letters + "_"
        valid_name = all((item in valid) for item in name)
        if not valid_name:
            return None
        result['name'] = name
        return result

    def _compute_address(self, section_info) -> SectionAddress:
        """
        section_info will be an array of SectioType data in the form of:
        [{'symbol':'ROMX', 'param':'$D123'},
         {'symbol':'BANK1', 'param':''}]
        This is just an example. In either case, 'param' can be blank.
        """
        if len(section_info) < 1:
            raise SectionDeclarationError("No section data.")

        sym = section_info[0]
        start_address, end_address =(
            self._sec_type.sectiontype_info(sym['symbol']))['addr']
        return SectionAddress(start=start_address, end=end_address)


if __name__ == "__main__":
    line = 'SECTION "game_vars", WRAM0[$C100]'
    section = Section.from_string(line)
    print(section)
