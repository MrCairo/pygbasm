#
## DS, DB, DW, DL declarations
#

from enum import Enum
from gbasm.exception import DefineDataError
from gbasm.conversions import ExpressionConversion

###############################################################################

class StorageType(Enum):
    SPACE = 0
    BYTE = 1
    WORD = 2
    LONG = 3


class _StorageBase:
    def __init__(self, size, data_set=None):
        self._item_size = size
        self._list = data_set
        self._data = []
        self._conv = ExpressionConversion()
        if not data_set:    # Allocate just one element of StorageType
            self._data.append(0)
        else:
            self._parse_list()

    def __iter__(self):
        self._roamer = 0
        return self

    def __next__(self):
        if self._roamer >= len(self._data):
            raise StopIteration
        item = self._data[self._roamer]
        self._roamer += 1
        return item

    def item_at_index(self, index):
        return self._data[index] if index < len(self._data) else None

    def _parse_list(self):
        if self._list == None:
            self._data.append(0x00)
        else:
            components = self._list.split(",")
            if self._item_size == StorageType.SPACE:
                self._to_space(components)
            elif self._item_size == StorageType.BYTE:
                self._to_bytes(components)
            elif self._item_size == StorageType.WORD:
                self._to_words(components)
            elif self._item_size == StorageType.LONG:
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
            size = self._conv.value_from_expression(components[0].strip())
        if len(components) >= 2:
            value = self._conv.value_from_expression(components[1].strip())
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
                        raise DefineDataError("A String cannot contain a string")
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

            value = self._conv.value_from_expression(item.strip())
            if value not in range(0,256):
                raise DefineDataError("DB should only allow byte value from 0x00 to 0xFF.")
            self._data.append(value)
            bytes_added += 1
        return bytes_added

    def _to_words(self, data_list):
        words_added = 0
        for item in data_list:
            num = self._conv.value_from_expression(item.strip())
            if num < 0 or num > 65535:
                raise DefineDataError(f"DB should only allow byte value from 0x00 to 0xFFFF.")
            self._data.append(num)
            words_added += 1
        return words_added

    def _to_longs(self, data_list):
        words_added = 0
        for item in data_list:
            num = self._conv.value_from_expression(item.strip())
            if num < 0 or num > 4294967295:
                raise DefineDataError("DB should only allow byte value from 0x00 to 0xFFFFFFFF.")
            self._data.append(num)
            words_added += 1
        return words_added

################################ End of class #################################
###############################################################################

class DataStorage(_StorageBase):
    """
    """
    _types = {
        "DS": StorageType.SPACE,
        "DB": StorageType.BYTE,
        "DW": StorageType.WORD,
        "DL": StorageType.LONG
        }

    def __init__(self, type_name, data_set=None):
        if type_name not in DataStorage._types:
            raise DefineDataError("Storage type must be DS, DB, DW, or DL")
        storage_size = DataStorage._types[type_name]
        super().__init__(storage_size, data_set)
