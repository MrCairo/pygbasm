import unittest
import os
import sys
import string
import inflect

###############################################################################
## Adds the develop gbasm package to the path. Pythonista tries to optimize
## anything in the Python Modules directories. Because of this, cached
## files from the gbasm will stick around. So, during develop, if the module
## is updated, it's not re-compiled, the cache is used instead. This leads
## to issues of modifying the package files in place and not being able to
## execute the change.
##
## tl;dr This code adds the develop version of gbasm to the Python module
## search path.
###############################################################################
from gbasm import Parser, ParserException, Instruction, InstructionPointer,\
                  InstructionSet, Constant
from gbasm.reader import Reader, FileReader, BufferReader

pynum = inflect.engine()
ins_set = InstructionSet()

ld_instr = """
	ld   b,b
	ld   b,c
	ld   b,d
	ld   b,e
	ld   b,h
	ld   b,l
	ld   b,(hl)
	ld   b,a
	ld   c,b
	ld   c,c
	ld   c,d
	ld   c,e
	ld   c,h
	ld   c,l
	ld   c,(hl)
	ld   c,a
	ld   d,b
	ld   d,c
	ld   d,d
	ld   d,e
	ld   d,h
	ld   d,l
	ld   d,(hl)
	ld   d,a
	ld   e,b
	ld   e,c
	ld   e,d
	ld   e,e
	ld   e,h
	ld   e,l
	ld   e,(hl)
	ld   e,a
	ld   h,b
	ld   h,c
	ld   h,d
	ld   h,e
	ld   h,h
	ld   h,l
	ld   h,(hl)
	ld   h,a
	ld   l,b
	ld   l,c
	ld   l,d
	ld   l,e
	ld   l,h
	ld   l,l
	ld   l,(hl)
	ld   l,a
	ld   (hl),b
	ld   (hl),c
	ld   (hl),d
	ld   (hl),e
	ld   (hl),h
	ld   (hl),l
	ld   (hl),a
	ld   a,b
	ld   a,c
	ld   a,d
	ld   a,e
	ld   a,h
	ld   a,l
	ld   a,(hl)
	ld   a,a
        ld   bc, $ffd2
        ld   (bc), a
        ld   (hl+),a
        ldh  ($aa),a
"""



class TestInstructionAssembler (unittest.TestCase):

    def test_compile_ld_register(self):
        reader = BufferReader(ld_instr)
        line = ""
        while line is not None:
            try:
                line = reader.read_line().strip(string.whitespace)
            except EOFError:
                line = None
            else:
                if line:
                    ins = Instruction(line)
                    res = ins.machine_code
                    self.assertTrue(res, f"Unknown instruction: {ins.instruction}")


    def test_compile_ins_with_address(self):
        reader = BufferReader("""jp    nz,$ffd2""")
        line = reader.read_line()
        ins = Instruction(line)
        result = ins.machine_code
        self.assertTrue(result,
                        "Unable to compile instruction with a 16-bit operand")
        self.report_binary_error(result, bytearray(b'\xc2\xd2\xff'))


    def test_8bit_operand(self):
        reader = BufferReader("""jr nz, &32""")
        line = reader.read_line()
        ins = Instruction(line)
        result = ins.machine_code
        self.assertTrue(result, "Unable to compile instruction")
        self.report_binary_error(result, bytearray(b'\x20\x1a'))


    def report_binary_error(self, expected, actual):
        self.assertEqual(len(expected), len(actual), "Parameters are different sizes. Fail!")

        for idx in range(0, len(expected)):
            num = pynum.number_to_words(idx)
            left = hex(actual[idx])
            right = hex(expected[idx])
            err = f"byte {num} is {left} and should be {right}"
            self.assertTrue(expected[idx] == actual[idx], err)


class TestInstructionPointer (unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ip = InstructionPointer()

    def test_IP_get_set(self):
        self.ip.location = 0x1000
        loc = self.ip.location
        self.assertTrue(loc == 0x1000, "IP could not be set.")

    def test_IP_move_relative_negatgive(self):
        self.ip = InstructionPointer()
        self.ip.location = 0x1000
        result = self.ip.move_relative(0xF5)
        self.assertTrue(result == True, "Was unable to move IP relative")
        loc = self.ip.location
        self.assertTrue(loc == 0x0FF5, "IP was not moved to the correct location.")
        result = self.ip.move_relative(0x0B)
        self.assertTrue(result == True, "Was unable to move IP relative")


    def test_IP_move_relative_positive(self):
        self.ip = InstructionPointer()
        self.ip.location = 0x1000
        result = self.ip.move_relative(0x0B)
        self.assertTrue(result == True, "Was unable to move IP relative")
        loc = self.ip.location
        self.assertTrue(loc == 0x100B, "IP was not moved to the correct location.")


    def test_IP_move_relative(self):
        self.ip = InstructionPointer()
        self.ip.location = 0x1000
        result = self.ip.move_relative(0x0B)
        self.assertTrue(result == True, "Was unable to move IP relative")
        loc = self.ip.location
        self.assertTrue(loc == 0x100B, "IP was not moved to the correct location.")
        result = self.ip.move_relative((-11 + 256) % 256) # -0x0b
        self.assertTrue(result == True, "Was unable to move IP relative")
        loc = self.ip.location
        self.assertTrue(loc == 0x1000, "IP was not moved to the correct location.")


if __name__ == "__main__":
    print("\nTesting Instruction methods")
    suite = unittest.TestLoader().loadTestsFromTestCase(TestInstructionAssembler)
    unittest.TextTestRunner(verbosity=2).run(suite)

    print("\nTesting InstructionPointer methods")
    suite = unittest.TestLoader().loadTestsFromTestCase(TestInstructionPointer)
    unittest.TextTestRunner(verbosity=2).run(suite)
