
class Reader (object):
    """
    Main subclass for the file readers. Not meant to be used directly
    rather used as a base class for polymorphic behavior.
    """
    def __init__(self):
        self._line=None
        self._eof=False
        self._read_position = 0

    @property
    def line(self) -> str:
        return self._line

    def read_line(self) -> str:
        pass

    def get_position(self):
        pass

    def set_position(self, position):
        pass

    def filename(self) -> str:
        pass

    def is_eof(self) -> bool:
        return self._eof

# end of class Reader


class BufferReader(Reader):
    """
    A Reader object that takes in a buffer and performs Reader operations on that
    buffer. An optional line_delimiter maybe specified which represents the EOL
    or end of line. By default, this value is "\n".
    """
    def __init__(self, buffer, line_delimiter="\n", debug=False):
        super().__init__()
        self._debug = debug
        self._buffer = buffer
        self._len = len(buffer)
        self._delimiter = line_delimiter
        self._dlen = len(self._delimiter)

    def read_line(self) -> str:
        if self._read_position < self._len:
            next_delim = self._buffer.find(self._delimiter,
                                           self._read_position)
            if self._debug:
                print(f"Slice = {self._read_position}:{next_delim}")
            if next_delim == -1:
                self._line = self._buffer[self._read_position:]
                self._read_position = self._len
                self._eof = True
            else:
                self._line = self._buffer[self._read_position:next_delim]
                self._read_position = (next_delim + self._dlen)
                if self._read_position >= self._len:
                    self._eof = True
            if self._debug:
                print(f"line == '{self._line}'")
            return self._line
        self._line = None
        self._eof = True
            #raise EOFError

    def get_position(self):
        """Returns the current read position in the file."""
        return self._read_position

    def set_position(self, position) -> bool:
        if position in range(0, self._len): #< self._len and position >= 0:
            self._read_position = position
            self._line = ""
            self._eof = False
            return True
        return False

    def filename(self) -> str:
        return "no_file"

############################ end of class BufferReader


class FileReader (Reader):
    """
    Class to encapsulate the reading of the source as a filesystem file.
    """
    def __init__(self, filename):
        super().__init__()
        self._filename = filename
        self._line = ""
        try:
            self._filestream = open(filename)
        except OSError:
            self._eof = True
            print(f"Could not open the file: {filename}")

    def read_line(self) -> str:
        """Reads one line from the data source.
        Line is a sequence of bytes ending with \n.
        """
        self._line = self._filestream.readline()
        if self._line:
            return self._line

        self._eof = True
        return None

    def get_position(self):
        return self._filestream.tell()

    def set_position(self, position):
        pos = self._filestream.seek(position)
        self._line = ""
        if pos == position:
            self._eof = False
        return pos

    def filename(self) -> str:
        """Returns the string name of the file being read."""
        return self._filename

############################ end of class FileReader
