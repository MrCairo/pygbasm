#
# DS, DB, DW, DL declarations
#

import imp
try:
    imp.find_module('gbasm_dev')
    from gbasm_dev import set_gbasm_path
    set_gbasm_path()
except ImportError:
    pass

from enum import Enum

from .constants import DIR, TOK, STOR
from .instruction_pointer import InstructionPointer as IP
from .conversions import ExpressionConversion as EC
from .exception import DefineDataError
from .lexer_parser import is_node_valid, BasicLexer

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

    def __init__(self, node: dict):
        self._parser = None
        if node[DIR] == STOR:
            self._tok = node[TOK]
            self._parser = StorageParser(node)
            return
        raise DefineDataError("The directive should be STORAGE but isn't")

    @classmethod
    def from_string(cls, text: str):
        """
        Creates a Storage object from a line of text containing the Storage
        directives
        """
        if text:
            tok = BasicLexer.from_string(text)
            tok.tokenize()
            return cls(tok.tokenized_list()[0])
        return cls({})

    def __str__(self):
        out = self._parser.type_name()
        out += self._parser.__str__()
        out += f"length: {len(self._parser)}"
        out += "\n"
        return out

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
        return STOR

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
                raise DefineDataError("Storage type must be "
                                      "DS, DB, DW, or DL")
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
            step = 1
            if self._tok[0] == "DW":
                step = 2
            elif self._tok[0] == "DL":
                step = 4
            for idx in range(0, len(self._data), step):
                val = self._data[idx]
                if step == 2:
                    val = val << 8
                    val += self._data[idx+1]
                    desc += f"{val:04x} "
                    idx += 1
                elif step == 4:
                    val = 0
                    for x in range(0, 4):
                        val += self._data[idx+x]
                        val <<= 8 if x < 3 else 0
                    desc += f"{val:08x} "
                    # Reduce the num of cols to account for the longer strings.
                    col += 1
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
        desc = f"Storage.from_string(\"{args}\")"
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
        return self._data

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
            size = EC().decimal_from_expression(components[0].strip())
        if len(components) >= 2:
            value = EC().decimal_from_expression(components[1].strip())
        # Validate
        valid = (size in range(0, 1024))
        valid = (value in range(0, 256))
        if valid:
            self._data = []
            for i in range(0, size):
                self._data.append(value)
            return size
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

            value = EC().decimal_from_expression(item.strip())
            if not 256 > value >= 0:
                msg = "DB should only allow byte value from 0x00 to 0xFF"
                raise DefineDataError(msg)
            self._data.append(value)
            bytes_added += 1
        return bytes_added

    def _to_words(self, data_list):
        words_added = 0
        for item in data_list:
            num = EC().decimal_from_expression(item.strip())
            if not 65536 > num >= 0:
                msg = f"DB should only allow byte value from 0x00 to 0xFFFF"
                raise DefineDataError(msg)
            vals = self._to_byte_array(num, 16)
            for v in vals:
                self._data.append(v)
            words_added += 1
        return words_added

    def _to_longs(self, data_list):
        words_added = 0
        for item in data_list:
            num = EC().decimal_from_expression(item.strip())
            if not 4294967296 > num >= 0:
                msg = "DB should only allow byte value from 0x00 to 0xFFFFFFFF"
                raise DefineDataError(msg)
            vals = self._to_byte_array(num, 32)
            for v in vals:
                self._data.append(v)
            words_added += 2
        return words_added

    def _to_byte_array(self, val, bits) -> bytearray:
        vals = bytearray()
        while bits > 0:
            vals.insert(0, val & 0xff)
            val = val >> 8
            bits -= 8
        return vals

################################ End of class #################################
###############################################################################


if __name__ == "__main__":
    IP().base_address = "$4000"
    x = Storage.from_string("DS 1")
    if x is not None:
        IP().location += len(x)
        print(x)
    s = Storage.from_string(
        "DB $00, $01, $01, $02, $03, $05, $08, $0d, 021, %00100010")
    if x is not None:
        IP().location += len(s)
        print(s)
    print(IP())
