"""
Global storage for the Gamy Boy Assembler
"""

from singleton_decorator import singleton
import gbasm.core.label as core

@singleton
class Global:

    def __init__(self):
        self._labels = core.Labels()
        self._global_labels = core.Labels()
