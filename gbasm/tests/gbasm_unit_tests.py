import unittest
import os
import sys
import string
import collections

os.environ['PYGBASM_HOME'] = os.path.dirname(os.path.realpath(__file__ + "/../.."))
print(sys.path)
import imp
try:
    imp.find_module('gbasm_dev')
    from gbasm_dev import set_gbasm_path
    set_gbasm_path()
    print(os.getenv('PYTHONPATH'))
except ImportError:
    pass

from gbasm.core import InstructionSet, BufferReader, Section, ParserException,\
    StorageType, Storage, Label, Labels, LabelUtils, LabelScope
from gbasm.core import BasicLexer, LexerResults, LexerTokens, LexicalAnalyzer
from gbasm.core import TOK, DIR, LBL, EQU, INST, SEC, STOR, MULT
from gbasm.assembler import CodeNode, CodeOffset, NodeProcessor, NodeType,\
    CodeNode, CodeOffset


class GbasmUnitTests(unittest.TestCase):

    def test_instructionSet(self):
        keys = InstructionSet().instruction_set.keys()
        self.assertTrue(keys is not None, "No keys returned.")

    def test_parseSectionWithOneType(self):
        test_buffer = """SECTION "OneType", ROMX"""
        sec = Section.from_string(test_buffer)
        self.assertTrue(sec.is_valid(), "Section should have parsed correctly but didn't")
        self.assertTrue(sec.name() == "ONETYPE", "Section should have parsed correctly but didn't")

    def test_sectionParsesSectioName (self):
        test_buffer = """SECTION "MySectionName", ROMX[$4000], BANK[$3], ALIGN[4]"""
        sec = Section.from_string(test_buffer)
        self.assertTrue(sec.is_valid(), "Section should have parsed correctly but didn't")
        self.assertTrue(sec.name() == "MYSECTIONNAME", "The section name was not equal to 'MYSECTIONNAME'")


    def test_parseFailsWithBadSectionName(self):
        buffer = """SECTION "Tes,ting", ROMX[$4000],BANK[1],ALIGN[4]"""
        with self.assertRaises(ParserException, msg="Paring the section SHOULD HAVE FAILED but didn't"):
            _ = Section.from_string(buffer)


    # def test_parseFromFile(self):
    #     p = Parser()
    #     p.load_from_file("test.asm")
    #     p.parse()
    #     self.assertTrue(p.sections[0].name == 'NewSection')
    #     print(f"Equates: {p.equates}")
    #     print("--- BEGIN LABELS DUMP ---")
    #     print(Labels().items())
    #     print("---- END LABELS DUMP ----")

    def test_DB_Storage(self):
        data = """DB $01, $ff, $ab, "This is a string" """
        dds = Storage.from_string(data)
        expected_len = 19
        self.assertTrue(len(dds) == expected_len,\
            f"Expected storage to be {expected_len} bytes.")
#        print(dds)

    def test_DS_Storage(self):
        dds = Storage.from_string("DS $14, $ff")
        expected_len = 20
        self.assertTrue(len(dds) == expected_len,\
            f"Expected storage to be {expected_len} bytes.")
#        print(dds)

    def test_DW_Storage(self):
        dds = Storage.from_string("DW $FFD2, $FFFF, $0000, $1000")
        expected_len = 8
        self.assertTrue(len(dds) == expected_len,\
            f"Expected storage to be {expected_len} bytes.")
#        print(dds)

    def test_DL_Storage(self):
        dds = Storage.from_string("DL $FFD2, $FFFF0000, $10000, $11000, $FFFFFFFF")
        expected_len = 20
        self.assertTrue(len(dds) == expected_len,\
            f"Expected storage to be {expected_len} bytes.")
#        print(dds)

class GbasmLabelTests(unittest.TestCase):
    ############################################################################
    # Label tests.
    def test_label_can_initialize(self):
        lbl = Label(".ThisIsALabel", 0x1000)
        self.assertTrue(lbl.value() == 0x1000, \
            "The expected value was 0x1000 but wasn't")

    def test_label_set_to_local_scope(self):
        lbl = Label(".ThisIsALabel:", 0xff)
        self.assertTrue(lbl.is_scope_global() is False,\
            "The label was expected to be local, not global in score.")

    def test_label_can_set_to_global_scope(self):
        lbl = Label(".ThisIsALabel::", 0xff)
        self.assertTrue(lbl.is_scope_global() is True,\
            "The label was expected to be global, not local in score.")


class GbasmCompileTests(unittest.TestCase):
    def test_section_IP_init(self):
        sec = Section.from_string("SECTION 'game_stuff', ROMX, BANK[$1]")
        self.assertTrue(sec.is_valid(), \
            "Unable to parse \"SECTION 'game_stuff', ROMX, BANK[$1]")

    def test_lexical_analyzer_with_string(self):
        line = "SECTION 'game_stuff', ROM0   ; Initial section"
        node = LexicalAnalyzer().analyze_string(line)
        self.assertTrue(node.directive() == SEC, \
            "analyze_string() returned unexpected results.")

    def test_lexical_analyzer_with_buffer(self):
        code1 = """
        SECTION 'game_stuff', ROM0   ; Initial section
        blahblahblah testing 123
        CLOUDX DB $FF,$00,$FF,$00,$FF,$00,$FF,$00,$FF,$00,$FF,$00,$FF,$00,$FF,$00
        MAXVAL EQU 65535
        .start:
          LD HL, $ffd2
          LD A,(HL+)
          DB $0A, $0B, $0C
          JR .end
          LD HL, SP+$45
          LD SP, $ffd2
        .end
          LD A, (HL-)
        """
        reader = BufferReader(code1)
        nodes = LexicalAnalyzer().analyze_buffer(reader)
        print("\n")
        print(nodes)

    def test_lexer_tokenize(self):
        code1 = """
        SECTION 'game_stuff', ROM0   ; Initial section
        CLOUDX DB $FF,$00,$FF,$00,$FF,$00,$FF,$00,$FF,$00,$FF,$00,$FF,$00,$FF,$00
        MAXVAL EQU 65535
        .start:
          LD HL, $ffd2
          LD A,(HL+)
          DB $0A, $0B, $0C
          JR .end
          LD HL, SP+$45
          LD SP, $ffd2
        .end
          LD A, (HL-)
          blahblahblah testing 123
        """
        # binary should look like:
        # 0000000 ff 00 ff 00 ff 00 ff 00 ff 00 ff 00 ff 00 ff 00
        # 0000010 21 d2 ff 2a 0a 0b 0c f8 45 31 d2 ff 18 f2 3a 00
        # 0000020 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00

        # np = NodeProcessor(BufferReader(""))
        # lex = BasicLexer.from_string(code1)
        # lex.tokenize()
        # for item in lex.tokenized_list():
        #     nodes = np.process_node(item)
        #     for n in nodes:
        #         print(n)


if __name__ == "__main__":
    print("\nTesting Parser methods")
    # suite = unittest.TestLoader().loadTestsFromTestCase(GbasmUnitTests)
    # unittest.TextTestRunner(verbosity=2).run(suite)
    # suite = unittest.TestLoader().loadTestsFromTestCase(GbasmLabelTests)
    # unittest.TextTestRunner(verbosity=2).run(suite)
    suite = unittest.TestLoader().loadTestsFromTestCase(GbasmCompileTests)
    unittest.TextTestRunner(verbosity=2).run(suite)

#    all_ins = InstructionSet.instance().instructions()
#    for ins in all_ins:
#_        print(ins)
