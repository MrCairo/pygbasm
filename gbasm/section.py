#
# Class that parses and contains information about a section.
# There can only be one section per file.
#
from collections import namedtuple
from .reader import Reader, FileReader, BufferReader
from .exception import SectionDeclarationError, SectionTypeError

###############################################################################

# Class that is just a namedtuple representing the Section start and end
# address.
class SectionAddress(namedtuple('SectionAddress', 'start, end')):
    pass



###############################################################################

class SectionType (object):

    def __init__(self):
        #                                             start, end
        #-------------------------------------------------------------
        self._sections = { "WRAM0": { 'id': 0, 'addr':(0xC000,0xCFFF) }, 
                           "VRAM":  { 'id': 1, 'addr':(0x8000,0x9FFF) },
                           "ROMX":  { 'id': 2, 'addr':(0x4000,0x7FFF) },
                           "ROM0":  { 'id': 3, 'addr':(0x0000,0x3FFF) },
                           "HRAM":  { 'id': 4, 'addr':(0xFF80,0xFFFE) },
                           "WRAMX": { 'id': 5, 'addr':(0xD000,0xDFFF) },
                           "SRAM":  { 'id': 6, 'addr':(0xA000,0xBFFF) },
                           "OAM":   { 'id': 7, 'addr':(0xFE00,0xFE9F) } }


    @property
    def sections(self):
        return self._sections
 
  
    def is_valid_sectiontype(self, sectionType):
        sec = sectionType.upper().strip()
        valid = (sec in self.sections.keys())
        if (valid == False):
            valid = (sec in ["BANK", "ALIGN"])
        return valid


    def sectiontype_id(self, sectiontype):
        section_id = None
        sec = sectiontype.upper().strip()
        if (self.is_valid_sectiontype(sectiontype)):
            pass

            
    def sectiontype_info(self, sectiontype):
        if sectiontype in self._sections:
            return self._sections[sectiontype]
        else:
            return None
        
        
###############################################################################
class Section (object):
    """
    Handles the parsing of a SECTION line.
    The return value of the "parseLine" is a dictionary
    """

    #
    # Init with the reader object. The line in the reader (or the one to be read)
    # must be the line with the SECTION keyword. If not, this class will be
    # considered invalid.
    #
    def __init__(self, reader: Reader):
        self._reader = reader
        self._sec_name = ""
        self._parsed = None
        self.start_pos = reader.get_position()
        self.sec_type = SectionType()
        self._parse_line()


    def __repr__(self):
        if self.is_valid:
            start, end = self.address_range
            desc = f"Section Name  '{self.name}'\n" \
                   f"Address Range '{start:04X} - {end:04X}'\n"
            return desc
        else:
            return "None"


    @property
    def name(self) -> str:
        return self._parsed['name'] if self._parsed is not None else None


    @property
    def address_range(self) -> SectionAddress:
        return self._parsed['address_range'] if self._parsed is not None else None


    @property
    def args(self) -> dict:
        return self._parsed['args'] if self._parsed is not None else None
        
        
    @property
    def is_valid(self) -> bool:
        return self._parsed is not None


    def _parse_line(self) -> dict:
        line = ""
        self._parsed = None
        if (self._reader.line is None and self._reader.is_eof() == False):
            line = self._reader.read_line()
        elif self._reader.is_eof():
            line = ""
        else:
            line = self._reader.line.strip().split(';')[0]
        parsed = self._validate_line(line)
        if len(parsed) > 0:
            self._parsed = parsed
        return parsed


    def _validate_line(self, line) -> dict:
        """
        SECTION "SectionNameInQuotes", ROMX[$4000],BANK[3]
        """
        # { 'section':'name', 'args':{'symbol':'ROMX', 'param':'$4000',...} }
        result = None 

        #
        # Input should look like:
        # SECTION "SectionNameInQuotes",SECTION_TYPE[$4000]
        #
        if line.upper().startswith("SECTION"):
            result = {}
            components = line.split(",", maxsplit=1)
            section = self._get_section_and_name(components[0])
            # There should be at least 2 elements. Any less represents an error
            
            if (section is None or len(components) != 2):
                print(components)
                raise SectionDeclarationError("Invalid Section format.", line_text=line)                
            else:
                # ['"sectionName"', "ROMX", "BANK[3]"]
                result["name"] = section["name"]
                # Get the symbols. There needs to be at least one.
                symbols = [] # An array of Dictionaries: { 'symbol':'ROMX', 'param':'$4000'}
                args = components[1].strip().split(",")
                for x in range(0, len(args)):
                    symDict = { "symbol":'', 'param':'' }
                    sym = args[x].split('[')
                    if (self.sec_type.is_valid_sectiontype(sym[0]) != True):
                        raise SectionTypeError(f"The section type '{sym[0]}' is not a valid section type.")
                    symDict["symbol"] = sym[0]
                    if (len(sym) > 1): # Will be something line "$4000]"
                        symDict['param'] = sym[1].strip("]")
                    symbols.append(symDict)
                result['args'] = symbols
                result['address_range'] = self._compute_address(symbols)
        return result

        
    def _get_section_and_name(self, text):
        # String should look like SECTION "SectionName" or SECTION 'SectionName'
        result = {}
        
        parts = text.split(" ", maxsplit=1)
        # There should be 2 elements. If _text_ doesn't contain any spaces, parts will
        # have only 1 element which is an error.
        if (len(parts) == 2 and "SECTION" in parts[0].upper()):
            result["label"] = parts[0].strip().upper()
        else:
            return None
        name = parts[1].strip().strip("\"'")
        validName = all(item.isalpha() for item in name)
        if (validName == False):
            return None
        result["name"] = name
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
        start_address, end_address = (self.sec_type.sectiontype_info(sym['symbol']))['addr']
        return SectionAddress(start=start_address, end=end_address)

