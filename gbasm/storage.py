#
## DS, DB, DW, DL declarations
#

from enum import Enum
from gbasm.exception import DefineDataError
from gbasm.conversions import ExpressionConversion as EC
from gbasm.basic_lexer import BasicLexer, is_node_valid
from gbasm.constants import DIR, TOK, STOR
from gbasm.instruction.instruction_pointer import InstructionPointer

###############################################################################

class StorageType(Enum):
    SPACE = 0
    BYTE = 1
    WORD = 2
    LONG = 3


class Storage:
    _roamer = 0
    _parser = None
    _tok: dict
    _base_address: int

    def __init__(self, node: dict):
        self._parser = None
        if node[DIR] == STOR:
            self._tok = node[TOK]
            self._parser = StorageParser(node)
            self._base_address = InstructionPointer().location
            return
        raise DefineDataError("The directive should be STORAGE but isn't")

    @classmethod
    def from_text(cls, text: str):
        """
        Creates a Storage object from a line of text containing the Storage
        directives
        """
        if text:
            tok = BasicLexer.from_text(text)
            tok.tokenize()
            return cls(tok.tokenized_list()[0])
        return cls({})

    def __str__(self):
        return self._parser.__str__()

    def __repr__(self):
        return self._parser.__repr__()

    def __iter__(self):
        self._roamer = 0
        return self

    def __next__(self):
        if self._roamer >= len(self._parser):
            raise StopIteration
        item = self._parser.data()[self._roamer]
        self._roamer += 1
        return item

    def __getitem__(self, position):
        return self._parser[position]

    def __len__(self):
        return len(self._parser)

    def storage_type(self):
        if self._parser:
            return self._parser.type_name()
        return None

    @staticmethod
    def typename():
        """Returns the string name of this class's type."""
        return "Storage"

    def to_bytes(self):
        return self._parser.data()


class StorageParser:
    """
    Parses storage types in tokenized format.
    """
    types = {
        "DS": StorageType.SPACE,
        "DB": StorageType.BYTE,
        "DW": StorageType.WORD,
        "DL": StorageType.LONG
        }

    def __init__(self, node: dict):
        self._data: bytearray = None
        self._node: dict = node
        self._tok: dict = {}
        self._type_name: str
        self._storage_size = 0
        if is_node_valid(node):
            self._tok = node[TOK]
            type_name = self._tok[0]
            if type_name not in self.types:
                raise DefineDataError("Storage type must be DS, DB, DW, or DL")
            self._storage_size = self.types[type_name]
            self._type_name = type_name
            self._data = bytearray()
            self._parse()

    def __str__(self):
        desc = "No Data"
        if self._data:
            desc = f"Type: {self._tok[0]}\n"
            desc += "Hex data:\n"
            desc += "  "
            col = 0
            for val in self._data:
                desc += f"VAL = {val}\n"
                if self._tok[0] == "DW":
                    desc += f"{val:04x} "
                elif self._tok[0] == "DL":
                    desc += f"{val:08x} "
                    col += 1  # This reduces the number of cols
                else:
                    desc += f"{val:02x} "
                col += 1
                if col > 7:
                    desc += "\n"
                    desc += "  "
                    col = 0
            desc += "\n"
        return desc

    def __repr__(self):
        args = self._tok[0] + " "
        for item in self._tok[1:-1]:
            args += item + ", "
        args += f"{self._tok[-1:][0]}"
        desc = f"Storage.from_text(\"{args}\")"
        return desc

    def __len__(self):
        if self._data:
            return len(self._data)
        return None

    def __getitem__(self, position: int):
        return self._data[position]  # if position < len(self) else None


    def type(self):
        """
        Returns the string type of this storage object. This can be DS, DB,
        DW, or DL.
        """
        if self._data:
            return self._tok[0]
        return None

    def type_name(self):
        return self._type_name

    def data(self):
        """Returns the storage data as an array of bytes."""
        return bytes(self._data)


    # -----=====< End of public methods >=====----- #

    def _parse(self):
        components = self._tok[1:]
        if self._storage_size == StorageType.SPACE:
            self._to_space(components)
        elif self._storage_size == StorageType.BYTE:
            self._to_bytes(components)
        elif self._storage_size == StorageType.WORD:
            self._to_words(components)
        elif self._storage_size == StorageType.LONG:
            self._to_longs(components)

    def _to_space(self, components):
        """
        This method is to accept no more than 2 parameters. The first
        is the number of bytes to allocate. The second, if provided,
        is the value to initialze the allocated space. If the second
        parameter is omitted, the default value is 0.
        If neither are provided, one one byte will be allocated and
        initialized to 0.
        """
        size = 1
        value = 0
        if len(components) >= 1:
            size = EC().value_from_expression(components[0].strip())
        if len(components) >= 2:
            value = EC().value_from_expression(components[1].strip())
        ## Validate
        valid = (size in range(0, 1024))
        valid = (value in range(0, 256))
        if valid:
            self._data = []
            for i in range(0, size):
                self._data.append(value)
            return size
            print(f"S, V = {size},{value}")
        err = "Invalid DS parameter(s): Size must ba number < 1024 and "\
              "value must be number < 256."
        raise DefineDataError(err)

    def _to_bytes(self, data_list):
        in_quotes = False
        bytes_added = 0
        for item in data_list:
            if in_quotes:
                # If we get a new item and we're still in_quotes, this
                # means that there was a comma(,) within the string. Just
                # continue processing as a string
                item = "," + item
            else:
                item = item.strip()
                # A string can be defined in a DB
                if item.startswith('"'):
                    if in_quotes:
                        msg = "A String cannot contain a string"
                        raise DefineDataError(msg)
                    in_quotes = True
                    item = item[1:]
            if in_quotes:
                if item.endswith('"'):
                    in_quotes = False
                    item = item[:-1]
                for char in item:
                    self._data.append(ord(char))
                    bytes_added += 1
                continue

            value = EC().value_from_expression(item.strip())
            if not 256 > value >= 0:
                msg = "DB should only allow byte value from 0x00 to 0xFF"
                raise DefineDataError(msg)
            self._data.append(value)
            bytes_added += 1
        return bytes_added

    def _to_words(self, data_list):
        words_added = 0
        for item in data_list:
            num = EC().value_from_expression(item.strip())
            if not 65536 > num >= 0:
                msg = f"DB should only allow byte value from 0x00 to 0xFFFF"
                raise DefineDataError(msg)
            self._data.append(num)
            words_added += 1
        return words_added

    def _to_longs(self, data_list):
        words_added = 0
        for item in data_list:
            num = EC().value_from_expression(item.strip())
            if not 4294967295 > num >= 0:
                msg = "DB should only allow byte value from 0x00 to 0xFFFFFFFF"
                raise DefineDataError(msg)
            self._data.append(num)
            words_added += 1
        return words_added


################################ End of class #################################
###############################################################################

if __name__ == "__main__":
    x = Storage.from_text("DS 1")
    print(x)
    s = Storage.from_text("DB $01, $02, $03, $04, $05, $06, $07, $07, $ff")
    print(s)
