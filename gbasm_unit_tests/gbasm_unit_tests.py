import unittest
import os
import sys
import string
import collections

from gbasm import *
from gbasm.parser import Parser, ParserException
from gbasm.instruction import Instruction, InstructionSet, InstructionPointer
#from gbasm import Reader, FileReader, BufferReader
#from gbasm import Section, SectionType, SectionAddress
from gbasm.storage import DataStorage
#from gbasm.label import Label, Labels

class GbasmUnitTests(unittest.TestCase):

    def test_instructionSet(self):
        keys = InstructionSet().instruction_set.keys()
        self.assertTrue(keys is not None, "No keys returned.")

    def test_parseSectionWithOneType(self):
        test_buffer = """SECTION "OneType", ROMX[$4000]"""
        reader = BufferReader(buffer=test_buffer)
        sec = Section(reader)
        self.assertTrue(sec.is_valid, "Section should have parsed correctly but didn't")
        self.assertTrue(sec.name == "OneType", "Section should have parsed correctly but didn't")


    def test_sectionParsesSectioName (self):
        test_buffer = """SECTION "MySectionName", ROMX[$4000], BANK[3], ALIGN[4]"""
        reader = BufferReader(buffer = test_buffer)
        sec = Section(reader)
        self.assertTrue(sec.is_valid, "Section should have parsed correctly but didn't")
        self.assertTrue(sec.name == "MySectionName", "The section name was not equal to 'MySectionName'")


    def test_parseFailsWithBadSectionName(self):
        buffer = """SECTION "Tes,ting", ROMX[$4000],BANK[1],ALIGN[4]"""
        reader = BufferReader(buffer=buffer)
        with self.assertRaises(ParserException, msg="Paring the section SHOULD HAVE FAILED but didn't"):
            sec = Section(reader)


    def test_parseFromFile(self):
        p = Parser()
        p.load_from_file("test.asm")
        p.parse()
        self.assertTrue(p.sections[0].name == 'NewSection')
        print(f"Equates: {p.equates}")
        print("--- BEGIN LABELS DUMP ---")
        print(Labels().items())
        print("---- END LABELS DUMP ----")

    def test_storage(self):
        data = """$01, $ff, $ab, "This is a string" """
        dds = DataStorage("DB", data)
        print("Bytes:")
        for item in dds:
            print(item, end=' ')

        print("\n\nStorage:")
        dds = DataStorage("DS", "$14, $ff")
        for item in dds:
            print(item, end=' ')

        print("\n\nWords:")
        dds = DataStorage("DW", "$FFD2, $FFFF, $0000, $1000")
        for item in dds:
            print(item, end=' ')

        print("\n\nLongs:")
        dds = DataStorage("DL", "$FFD2, $FFFF0000, $10000, $11000, $FFFFFFFF")
        for item in dds:
            print(item, end=' ')


if __name__ == "__main__":
    print("\nTesting Parser methods")
    suite = unittest.TestLoader().loadTestsFromTestCase(GbasmUnitTests)
    unittest.TextTestRunner(verbosity=2).run(suite)

#    all_ins = InstructionSet.instance().instructions()
#    for ins in all_ins:
#_        print(ins)
