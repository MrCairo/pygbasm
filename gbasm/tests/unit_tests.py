"""
gbasm unit tests
"""
import unittest
import json, os, sys, string
import random
from gbasm.label import Label, Labels
from gbasm.instruction import Instruction, InstructionSet

_instruction_set = None
_ins_processed_count = 0

class TestLabelMethods(unittest.TestCase):

    def test_create_label(self):
        label = Label('.GOTO_LABEL:', 0x1000)
        self.assertIsNotNone(label, "Couldn't create the Label")

    def test_label_no_name(self):
        try:
            _ = Label(None, 0x1000)
        except ValueError:
            pass
        else:
            self.fail("Should have raised a ValueError exception.")

    def test_label_invalid_name(self):
        try:
            _ = Label("!!!", 0x2000)
        except ValueError:
            pass
        else:
            self.fail("Should have raised a ValueError exception.")

    def test_label_invalid_constant(self):
        try:
            _ = Label(".label", 0xabcd)
        except ValueError:
            pass
        else:
            self.fail("Should have raised a ValueError exception.")

    def test_label_clean_name(self):
        label = Label(".CamelCase::", 0xff)
        self.assertEqual(label.clean_name(), "CamelCase")

    def test_label_original_name(self):
        key = ".CamelCase::"
        label = Label(key, 0xab)
        self.assertEqual(label.name(), key)

    def test_label_value(self):
        label = Label("TestConstant", 0xffd2)
        self.assertEqual(label.value(), 0xffd2)

    def test_label_default_const(self):
        label = Label("ShouldBeConst", 255)
        self.assertTrue(label.is_constant)

    def test_label_default_non_const(self):
        label = Label(".ShouldNotBeConst:", 32768)
        self.assertFalse(label.is_constant)

    def test_label_force_const(self):
        label = Label(".ShouldNotBeConst:", 32768, force_const=True)
        self.assertTrue(label.is_constant)
        label = Label("ShouldBeConst2", 128, force_const=False)
        # Should be const. Fale == don't force to const.
        # So, if the value is supposed to be const, is stays that way
        self.assertTrue(label.is_constant)

    def test_label_is_global(self):
        label = Label(".GlobalLabel::", 0x50)
        self.assertTrue(label.is_scope_global())

    def test_label_is_local(self):
        label = Label(".NonGlobalLabel:", 0x99)
        self.assertFalse(label.is_scope_global())

    # --------========[ End of TestLabelMethods class ]========-------- #


class TestLabelContainer(unittest.TestCase):

    def setUp(self):
        Labels().remove_all()

    def tearDown(self):
        Labels().remove_all()

    def test_add_label(self):
        self.assertTrue(len(Labels().items()) == 0)
        label = Label(".Label:", 0x1000)
        Labels().add(label)
        self.assertTrue(len(Labels().items()) == 1)

    def test_remove_label(self):
        self.assertTrue(len(Labels().items()) == 0)
        label = Label(".testLabel::", 0x2000)
        Labels().add(label)
        self.assertTrue(len(Labels().items()) == 1)
        Labels().remove(label)
        self.assertTrue(len(Labels().items()) == 0)

    def test_label_items(self):
        self.assertTrue(len(Labels().items()) == 0)
        for i in range(0, 100):
            txt = ".testLabel%d::" % i
            label = Label(txt, (0x1000 + i) )
            Labels().add(label)
        self.assertEqual(len(Labels().items()), 100)

    def test_remove_all_labels(self):
        self.assertTrue(len(Labels().items()) == 0)
        for i in range(0, 100):
            txt = ".testLabel%d::" % i
            label = Label(txt, (0x1000 + i))
            Labels().add(label)
        self.assertEqual(len(Labels().items()), 100)
        Labels().remove_all()
        self.assertTrue(len(Labels().items()) == 0)

    def test_label_lookup(self):
        key = ".GOTO_LABEL::"
        label = Label(key, 0x1000)
        Labels().add(label)
        self.assertIsNotNone(Labels()[label.clean_name()])

    # --------========[ End of class ]========-------- #


class TestInstructionMethods(unittest.TestCase):

    def test_all_instructions(self):
        global _ins_processed_count
        all_ins = ['ADD', 'AND', 'CALL', 'CCF', 'CP', 'CPL', 'DAA', 'DEC',
                   'DI', 'EI', 'INC', 'JP', 'JR', 'LD', 'LDH', 'NOP', 'OR',
                   'POP', 'PUSH', 'RET', 'RETI', 'RLA', 'RRA', 'RRCA',
                   'RST', 'SCF', 'STOP', 'SUB', 'XOR', 'HALT', 'ADC',
                   'SBC', 'RLC', 'RRC', 'RL', 'RR', 'SLA', 'SRA', 'SWAP',
                   'SRL', 'BIT', 'RES', 'SET']
        print("Testing all instructions.")
        _ins_processed_count = 0
        for mnemonic in all_ins:
            print(f".", end="")
            err = test_instruction(mnemonic)
            self.assertIsNone(err, err)
        print(f"\nTested {_ins_processed_count} instructions\n")

# -----=====< Unit test suites >=====----- #

def label_suite():
    suite = unittest.TestSuite()
    suite.addTest(TestLabelMethods('test_create_label'))
    suite.addTest(TestLabelMethods('test_label_invalid_constant'))
    suite.addTest(TestLabelMethods('test_label_no_name'))
    suite.addTest(TestLabelMethods('test_label_invalid_name'))
    suite.addTest(TestLabelMethods('test_label_clean_name'))
    suite.addTest(TestLabelMethods('test_label_original_name'))
    suite.addTest(TestLabelMethods('test_label_value'))
    suite.addTest(TestLabelMethods('test_label_default_const'))
    suite.addTest(TestLabelMethods('test_label_default_non_const'))
    suite.addTest(TestLabelMethods('test_label_force_const'))
    suite.addTest(TestLabelMethods('test_label_is_global'))
    suite.addTest(TestLabelMethods('test_label_is_local'))
    # Labels Container Tests
    suite.addTest(TestLabelContainer('test_add_label'))
    suite.addTest(TestLabelContainer('test_remove_label'))
    suite.addTest(TestLabelContainer('test_label_items'))
    suite.addTest(TestLabelContainer('test_remove_all_labels'))
    suite.addTest(TestLabelContainer('test_label_lookup'))
    return suite

def instruction_suit():
    suite = unittest.TestSuite()
    suite.addTest(TestInstructionMethods('test_all_instructions'))
    return suite


# -----=====< Utility Functions >=====----- #
#                                           #
def load_instruction_set() -> dict:
    """
    Loads the LR35902 instruction set from the JSON
    file located in the same directory as this script.
    """
    filedir = os.path.realpath(
        os.path.join(os.getcwd(),
                     os.path.dirname(__file__)))
    json_filename = f'{filedir}/../instruction/gbz80-hex.json'
    if os.path.exists(json_filename):
        fh = open(json_filename)
        return json.load(fh)
    return None

def test_instruction(mnemonic:str) -> str:
    """
    Tests an instruction set of a specific mnemonic. So, if an "LD"
    is used, all LD instructions are tested.
    """
    global _ins_processed_count
    ins_list = get_instructions_by_mnemonic(mnemonic)
    if ins_list:
        for ins in ins_list:
            line = ins["code_line"]
            # print(line, end="")
            code = Instruction.from_string(line)
            if code.is_valid():
                _ins_processed_count += 1
                desc = "  -- bin: "
                for byte in code.machine_code():
                    desc += f"{byte:02x} "
                # print(desc)
                continue
            return f"Instruction {line} failed."
    return None

def get_instructions_by_mnemonic(mnemonic: str) -> dict:
    found_list = []
    for key in _instruction_set.keys():
        node = _instruction_set[key]
        if node["mnemonic"] == mnemonic:
            line = mnemonic
            # Fill in placeholders (i.e. d8, a16) with random hex values
            repl = None
            if "operand1" in node:
                repl = fill_placeholder(node["operand1"])
                if repl:
                    node["operand1"] = repl
                line += f" {node['operand1']}"
            if "operand2" in node:
                repl = fill_placeholder(node["operand2"])
                if repl:
                    node["operand2"] = repl
                line += f" {node['operand2']}"
            node["code_line"] = line
            found_list.append(node)
    return found_list

def rnd_hex_num(num_bytes: int) -> str:
    bits = num_bytes * 8
    if bits not in range(0, 17):
        return ""
    maximum = (2**bits) - 1
    num = random.randrange(0, maximum)
    if num_bytes == 1:
        return f"${num:02x}"
    return f"${num:04x}"

def fill_placeholder(op: str) -> str:
    repl = None
    if op:
        eight = ["d8", "a8", "r8"]
        sixteen = ["d16", "a16"]
        rnd8 = rnd_hex_num(1)
        rnd16 = rnd_hex_num(2)
        for b in eight:
            if b in op:
                repl = op.replace(b, rnd8)
                break
        if not repl:
            for b in sixteen:
                if b in op:
                    repl = op.replace(b, rnd16)
                    break
    return repl

if __name__ == "__main__":
    _instruction_set = load_instruction_set()
    _ins_processed_count = 0
    runner = unittest.TextTestRunner()
    runner.run(label_suite())
    runner.run(instruction_suit())
