"""
Global storage for the Gamy Boy Assembler
"""

from singleton_decorator import singleton_decorator
from Label import Label, Labels

@singleton
class Global:

    def __init__(self):
        self._labels = Labels()
        self._global_labels = Labels()
