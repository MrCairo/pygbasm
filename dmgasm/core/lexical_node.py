#
#
from typing import Dict
from .constants import DIR, TOK, BAD, MULT


class LexicalNode:
    """
    LexicalNode is a specialized object or more like a pseudo dictionary.
    The LexicalNode contains only a directive string and a token dictionary.
    As a result, this object ONLY allows the keys of DIR and TOK to be read
    Additionally, the value of DIR must be of type str (or None) and TOK
    must be of type dict (or None).

    As mentioned above, the LexicalNode has a __getitem()__ which means
    that it is possible to use the lexical node like

        node = LexicalNode(directive, tokens)
        print(node[TOK])
        print(node[DIR])
        node[TOK] = "Test"      # Raises an IndexError. Set is not possible

    Parameters:
    - directive (str): The type of construct that the TOK value contains which
            can be an STOR, INST, LBL, MULT, or None. This is no check for the
            value of the directive other than it has to be a str or None.
    - tokens (list, dict): A dict object that contains the tokenized values of
            a single line of source code parsed by the LexicalAnalyzer. This
            is generally an array but can also be a dictionary object. If the
            token is an array, it is also possible that the tokens are an
            array of LexicalNodes. This is also valid.
    """

    def __init__(self, directive: str = None, tokens=None):
        # The intention is to make this object immutable but we're not using
        # the new 3.7 feature for a frozen data class.
        # Be a good neighbor and don't access underscore variables outside of
        # the scope of this class :)
        self._data = {DIR: directive, TOK: tokens}
        if not LexicalNode.is_valid_node(self):
            raise TypeError(self._data)

    def __getitem__(self, key):
        if key in [TOK, DIR]:
            return self._data[key]
        raise IndexError(key)

    def __contains__(self, key) -> bool:
        if key in [DIR, TOK]:
            return key in self._data.keys()
        return False

    #
    # Should this be a mutable class? For now, NO and we try our best to do
    # that here.
    #
    def __setitem__(self, key, value):
        raise IndexError

    def __repr__(self):
        desc = f"{self._repr_of_instance()}\n"
        # Check for embedded LexicalNode
        tokens = self.token()
        if tokens is not None and type(tokens) is list:
            if len(tokens) and tokens[0] is dict:
                if LexicalNode.is_valid_node(tokens[0]):
                    desc += ">>> inner node >>>\n"
                    desc += f">>> {item._repr_of_instance()}\n"
                else:
                    desc += ">> INVALID LexicalNode >>\n"
                    return desc
        return desc

    def __str__(self):
        desc = "\n LexicalNode: \n"
        desc += f"    directive = {self.directive()}\n"
        desc += f"    tokens = {self.token()}"
        if self._data[TOK] is not None:
            item = self._data[TOK]
            if DIR in item and TOK in item:
                x = LexicalNode(item[DIR], item[TOK])
                desc += "\n>>> Inner LexicalNode\n" + x.__str__()
        return desc

    # def __setitem__(self, key, value):
    #     if key == DIR:
    #         if type(value) is str or value is None:
    #             self._data[DIR] = value
    #         raise TypeError(value)
    #     elif key == TOK:
    #         if type(value) is dict or value is None:
    #             self._data[TOK] = value
    #         raise TypeError(value)
    #     else:
    #         raise IndexError(key)

    def directive(self) -> str:
        """Returns the current directive (DIR) value. This value can also be
        accessed as 'variable[DIR]'. It is possible for this value to be
        None."""
        return self._data[DIR]

    def token(self):
        """Returns the current token (TOK) value. This value can also be
        accessed as 'variable[TOK]'. It is possible for this value to be
        None."""
        return self._data[TOK]

    def value(self) -> Dict:
        """Returns the current LexicalNode as a raw dictionary. Please note
        that this is a copy of the LexicanNode and not a reference to the
        actual values."""
        return {DIR: self[DIR], TOK: self[TOK]}

    def _repr_of_instance(self) -> str:
        return f"LexicalNode(\"{self._data[DIR]}\", \"{self._data[TOK]}\")"

    @classmethod
    def is_valid_node(cls, node) -> bool:
        valid = type(node) is LexicalNode
        if valid:
            valid = TOK in node and DIR in node
        if valid:
            valid = node[DIR] is not BAD
        if valid and node[DIR] is None:
            valid = node[DIR] is None and node[TOK] is None
        if valid:
            valid = DIR in node and TOK in node
        if valid and node[TOK] is not None:
            valid = (type(node[TOK]) is list or type(node[TOK]) is dict or
                     type(node[TOK]) is str or type(node[TOK] is LexicalNode))
        if valid and node[DIR] is MULT:
            if type(node[TOK]) is LexicalNode:
                newNode = node[TOK]
                valid = LexicalNode.is_valid_node(newNode)
        return valid
