#
#
#
# if __name__ == "__main__":
#     import gbasm_dev
#     gbasm_dev.include_developer_path()

import string
from singleton_decorator import singleton
from gbasm.instruction import InstructionPointer


###############################################################################
class Label ():
    """Represents a label which is used to represent an address or constant.
    """

    LOCAL_SCOPE = 0
    GLOBAL_SCOPE = 1
    first_chars = string.ascii_letters + "."
    valid_chars = string.ascii_letters + ".:"

    def __init__(self, name: str, value: int):
        """Represents a label which is, in turn, used to represent an address
        or a constant in the program.
        - name:
            The text identifier of the Label
        - value:
            A numeric 16-bit value that can represent a value up to 16-bits.

        Optional:
        - constant:

            Constants can only be alpha character. This means that a constant
            CANNOT begine with a "." or end with a ":".

            Note: The value of a contant can be less than 0 or greater than 65535.
        - base:
            A numeric address (can be an expression like $FFD2). This defaults
            to the current identified SECTION as reported by the InstructionPointer
            object.
        """
        if not name:
            raise ValueError

        self._constant = False

        # Valid:
        #   .label:      (local non-constant label)
        #   .label::     (global non-constant label)
        #   label        (EQU local constant label)
        if name.endswith(":") and name.startswith("."):
            self._scope = Label.LOCAL_SCOPE
        elif name.endswith("::") and name.startswith("."):
            self._scope = Label.GLOBAL_SCOPE
        elif (name[0].isalpha() and name.isalnum()): # Must be an EQU?
            self._scope = Label.LOCAL_SCOPE
            self._constant = True
        else:
            raise ValueError

        # Label now must be an EQU since it doesn't have a scope character
        # Local/Global scope labels must start with a '.'
        # EQU labels are only alpha-numeric
        if name.startswith(".") and self.is_constant:
            raise ValueError

        self._original_label = name
        self._clean_label = (name.lstrip(" .")).rstrip(":. ")
        self._value = value
        self._base_address = InstructionPointer().base_address


    def __repr__(self):
        is_const = "---"
        is_const = "Yes" if self._constant == True else "No"
        scope = "local" if self._scope == Label.LOCAL_SCOPE else "global"
        desc = f"\nLabel: {self.name}\nvalue: 0x{self.value:04x} "
        desc += f"is constant: {is_const}"
        desc += f"\nScope: {scope}"
        return desc


    @property
    def clean_name(self):
        """Returns the cleaned valid label stripped of the first and
        last label characters"""
        return self._clean_label

    @property
    def name(self):
        """Returns the original value of the valid label. It will
        start with a '.'"""
        return self._original_label

    @property
    def value(self):
        """Returns the value passed when the object was created."""
        return self._value

    @property
    def is_constant(self):
        """Determines if the value is to be considered a constant or
        not."""
        return self._constant

    @is_constant.setter
    def is_constant(self, new_value):
        """Determines if the value is to be considered a constant or
        not."""
        self._constant = True if new_value is True else False

    def is_unresolved(self):
        return False

    def is_scope_global(self):
        return self._scope == self.GLOBAL_SCOPE


######################################################################


@singleton
class Labels(dict):
    """A specialized dictionary that maintains all labels.

    Labels()[a_key] = a_label
    a_label = Labels()[a_key]

    """
    first_chars = string.ascii_letters + "."
    valid_chars = string.ascii_letters + ".:"

    _labels = {}

    def __init__(self):
        super().__init__()
        self._labels = dict()

    def __repr__(self):
        desc = ""
        if self._labels:
            for label in self._labels:
                desc = label.__repr__()
        return desc

    def __getitem__(self, key: str):
        if key:
            key = (key.lstrip(".")).rstrip(":.")
        if key in self._labels.keys():
            return None if key not in self._labels \
                else self._labels[key]
        return None

    def __setitem__(self, key: str, value: Label):
        if not isinstance(value, Label):
            raise TypeError
        self._labels[value.clean_name] = value

    def find(self, key: str) -> Label:
        """Equal to the __get__() index function."""
        return self[key]

    def add(self, label: Label):
        if label is not None:
            self._labels[label.clean_name] = label

    def items(self) -> dict:
        return self._labels


############### end of Labels class ###############

if __name__ == "__main__":
    def test_label():
        label = Label('.GOTO_LABEL:', 0x1000)
        if label is None:
            print("Unable to create a label")
        else:
            Labels().add(label)

        if Labels()['GOTO_LABEL']:
            print("Label was found.")
        else:
            print("Unable to find the label.")
            print(Labels())

    test_label()
