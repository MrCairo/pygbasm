"""
Class(es) that implements a Z80/LR35902 instruction and Instruction Set
"""

from singleton_decorator import singleton
from gbasm.instruction.registers import Registers
import json
import os


@singleton
class InstructionSet():
    """ Represents the entire Z80 instruction set """

    variable_operands = ["d8", "d16", "a8", "a16", "r8"]
    """
    d8  = Immediate 8-bit data.
    d16 = Immediate 16-bit data.
    a8  = 8 bit unsigned data, which are added to $FF00 in
          certain instructions (replacement for missing IN
          and OUT instructions.
    a16 = 16-bit address
    r8  = 8-bit signed data which are added to the program
          counter.
    """

    def __init__(self):
        self._instructions = {
            "ADD": {"HL":  {"BC": {"!": 0x09},
                            "DE": {"!": 0x19},
                            "HL": {"!": 0x29},
                            "SP": {"!": 0x39}},
                    "A": {"d8": {"!": 0xc6}},
                    "SP": {"r8": {"!": 0xe8}}},
            # More ADD A,rr instructions in _build_ASXOC_REG_instructions
            "AND": {"d8": {"!": 0xe7}},
            # "AND"   -- remainder in _build_ASXOC_REG_instructions
            # "ADC"   -- in _build_ASXOC_REG_instructions
            # "BIT"   -- in _build_CB_instructions
            "CALL": {"NZ": {"a16": {"!": 0xc4}},
                     "NC": {"a16": {"!": 0xd4}},
                     "Z": {"a16": {"!": 0xcc}},
                     "C": {"a16": {"!": 0xdc}},
                     "a16": {"!": 0xcd}},
            "CCF": {"!": 0x3f},
            "CP": {"d8": {"!": 0xfe}},
            # "CP"   -- remaining in _build_CP_instructions()
            "CPL": {"!": 0x2f},
            "DAA": {"!": 0x27},
            "DEC": {"B": {"!": 0x05},
                    "BC": {"!": 0x0b},
                    "C": {"!": 0x0d},
                    "D": {"!": 0x15},
                    "DE": {"!": 0x1b},
                    "E": {"!": 0x1d},
                    "H": {"!": 0x25},
                    "HL": {"!": 0x2b},
                    "L": {"!": 0x2d},
                    "(HL)": {"!": 0x35},
                    "SP": {"!": 0x3b},
                    "A": {"!": 0x3d}},
            "DI": {"!": 0xf3},
            "EI": {"!": 0xfb},
            # "HALT" -- in _build_LD_REG_instructions
            "INC": {"BC": {"!": 0x03},
                    "B": {"!": 0x04},
                    "C": {"!": 0x0c},
                    "DE": {"!": 0x13},
                    "D": {"!": 0x14},
                    "E": {"!": 0x1c},
                    "HL": {"!": 0x23},
                    "H": {"!": 0x24},
                    "L": {"!": 0x2c},
                    "SP": {"!": 0x33},
                    "(HL)": {"!": 0x34},
                    "A": {"!": 0x3c}},
            "JP": {"NZ": {"a16": {"!": 0xc2}},
                   "a16": {"!": 0xc3},
                   "Z": {"a16": {"!": 0xca}},
                   "NC": {"a16": {"!": 0xd2}},
                   "C": {"a16": {"!": 0xda}},
                   "(HL)": {"!": 0xe9}},
            "JR": {"r8": {"!": 0x18},
                   "NZ": {"r8": {"!": 0x20}},
                   "Z": {"r8": {"!": 0x28}},
                   "NC": {"r8": {"!": 0x30}},
                   "C": {"r8": {"!": 0x38}}},
            "LD":  {"BC": {"d16": {"!": 0x01}},
                    "DE": {"d16": {"!": 0x11}},
                    "HL": {"d16": {"!": 0x21},
                           "SP+r8": {"!": 0xf8}},
                    "SP": {"d16": {"!": 0x31}},
                    "(BC)": {"A": {"!": 0x02}},
                    "(DE)": {"A": {"!": 0x12}},
                    "(HL+)": {"A": {"!": 0x22}},
                    "(HL-)": {"A": {"!": 0x32}},
                    "B": {"d8": {"!": 0x06}},
                    "D": {"d8": {"!": 0x16}},
                    "H": {"d8": {"!": 0x26}},
                    "(HL)": {"d8": {"!": 0x36}},
                    "(C)" : {"A": {"!": 0xe2}},
                    "(a16)": {"SP": {"!": 0x08},
                              "A": {"!": 0xea}},
                    "A": {"(C)": {"!": 0xf2},
                          "(BC)": {"!": 0x0a},
                          "(DE)": {"!": 0x1a},
                          "(HL+)": {"!": 0x2a},
                          "(HL-)": {"!": 0x3a},
                          "d8": {"!": 0x3e},
                          "(a16)": {"!": 0xfa}},
                    "C": {"d8": {"!": 0x0e}},
                    "E": {"d8": {"!": 0x1e}},
                    "L": {"d8": {"!": 0x2e}}},
            # "LD"   -- Remainder in _build_LD_REG_instructions
            "LDH": {"({a8})": {"A": {"!": 0xe0}},
                    "A": {"(a8)": {"!": 0xf0}}},
            "NOP": {"!": 0x00},
            "OR": {"d8": {"!": 0xf6}},
            # "OR"   -- remainder in _build_ASXOC_REG_instructions
            "POP": {"BC": {"!": 0xc1},
                    "DE": {"!": 0xd1},
                    "HL": {"!": 0xe1},
                    "AF": {"!": 0xf1}},
            "PUSH": {"BC": {"!": 0xc5},
                     "DE": {"!": 0xd5},
                     "HL": {"!": 0xe5},
                     "AF": {"!": 0xf5}},
            # "RES"  -- in _build_CB_instructions
            "RET": {"NZ": {"!": 0xc0},
                    "Z": {"!": 0xc8},
                    "NC": {"!": 0xd0},
                    "C": {"!": 0xd8},
                    "!": 0xc9},
            "RETI": {"!": 0xd9},
            # "RL"   -- in _build_CB_instructions
            "RLA": {"!": 0x17},
            # "RLC"  -- in _build_CB_instructions
            # "RLCA" : self._op_RLCA,
            # "RR"   -- in _build_CB_instructions
            "RRA": {"!": 0x1f},
            # "RRC"  -- in _build_CB_instructions
            "RRCA": {"!": 0x0f},
            "RST": {"#$00": {"!": 0xc7},
                    "#$08": {"!": 0xcf},
                    "#$10": {"!": 0xd7},
                    "#$18": {"!": 0xdf},
                    "#$20": {"!": 0xe7},
                    "#$28": {"!": 0xef},
                    "#$30": {"!": 0xf7},
                    "#$38": {"!": 0xff}},
            # "SBC"  -- in _build_ASXOC_REG_instructions
            "SCF": {"!": 0x37},
            # "SET"  -- in _build_CB_instructions
            # "SLA"  -- in _build_CB_instructions
            # "SRA"  -- in _build_CB_instructions
            # "SRL"  -- in _build_CB_instructions
            "STOP": {"!": 0x10},
            "SUB": {"d8": {"!", 0xd6}},
            # "SUB"  -- remaining in _build_ASXOC_REG_instructions
            # "SWAP" -- in _build_CB_instructions
            "XOR": {"d8": {"!": 0xee}} # rest in _build_ASXOC_REG_instructions
        }
        self._build_LD_REG_instructions()
        self._build_ASXOC_REG_instructions()
        self._build_CB_instructions()
        self._build_CP_instructions()
        self._ins_detail = self._load_ins_detail()
        self._mnemonics = self._instructions.keys()

        # -----=====< End of __init__() >=====----- #

    def instruction_from_mnemonic(self, mnemonic: str) -> dict:
        """Returns the instruction definition dict for the given
        mnemonic"""
        if mnemonic is not None:
            if mnemonic in self._instructions:
                return self._instructions[mnemonic]
        return None

    def instruction_detail_from_byte(self, byte: str) -> dict:
        if byte in self._ins_detail:
            return self._ins_detail[byte]
        return None

    @property
    def instruction_set(self):
        """ Returns the Z80 instruction set as a dictionary. """
        return self._instructions

    def is_mnemonic(self, mnemonic_string: str) -> bool:
        if mnemonic_string:
            return mnemonic_string.upper() in self._mnemonics
        return False

    #                                             #
    # -----=====<  Private Functions  >=====----- #

    def _build_CP_instructions(self):
        start = 0xb8
        index = 0
        mn = "CP"
        existing = {} if mn not in self._instructions \
            else self._instructions[mn]
        top = {}
        for reg in Registers().working_registers():
            top[reg] = {"!": start + index}
        self._instructions[mn] = self._merge(existing, top)

    def _build_LD_REG_instructions(self):
        start = 0x40
        index = 0
        mn = "LD"
        existing = {} if mn not in self._instructions \
            else self._instructions[mn]
        for to_reg in Registers().working_registers():
            tr = {} if to_reg not in existing else existing[to_reg]
            fr = {}
            for from_reg in Registers().working_registers():
                address = start + index
                index += 1
                if to_reg == "(HL)" and from_reg == "(HL)":
                    continue
                fr = {"!": address}
                tr[from_reg] = fr if from_reg not in tr else self._merge(
                    tr[from_reg], fr)
            existing[to_reg] = tr
        self._instructions[mn] = existing
        self._instructions["HALT"] = {"!": 0x76}

    def _build_ASXOC_REG_instructions(self):
        # Mnemonics that set the accumulator
        operations = ['ADD', 'ADC', 'SBC']
        starts = [0x80, 0x88, 0x98]
        index = 0
        for idx in range(len(operations)):
            mn = operations[idx]
            start = starts[idx]
            index = 0
            existing = {} if mn not in self._instructions \
                else self._instructions[mn]
            a_reg = {'A': {}}
            acc = {} if 'A' not in existing else existing['A']
            for reg in Registers().working_registers():
                acc[reg] = {"!": (start + index)}
                index += 1
            a_reg['A'] = self._merge(a_reg['A'], acc)
            self._instructions[mn] = self._merge(existing, a_reg)

        # Mnemonics that DON'T set the accumulator
        operations = ['SUB', 'AND', 'XOR', 'OR', 'CP']
        starts = [0x90, 0xa0, 0xa8, 0xb0, 0xb8]
        for idx in range(len(operations)):
            mn = operations[idx]
            start = starts[idx]
            index = 0
            existing = {} if mn not in self._instructions \
                else self._instructions[mn]
            op = {}
            for reg in Registers().working_registers():
                op[reg] = {"!": (start + index)}
                index += 1
            self._instructions[mn] = self._merge(existing, op)

    def _build_CB_instructions(self):
        start = 0xCB00
        index = 0

        operations = ['RLC', 'RRC', 'RL', 'RR', 'SLA', 'SRA', 'SWAP', 'SRL']
        for mn in operations:
            existing = {} if mn not in self._instructions \
                else self._instructions[mn]
            op = {}
            for reg in Registers().working_registers():
                address = start + index
                op[reg] = {"!": address}
                index += 1
            self._instructions[mn] = self._merge(existing, op)
        #
        # Build BIT instructions
        #
        operations = ['BIT', 'RES', 'SET']
        for mn in operations:
            existing = {} if mn not in self._instructions \
                else self._instructions[mn]
            top = {}
            for bit in range(8):
                op = {}
                for reg in Registers().working_registers():
                    op[reg] = {"!": (start + index)}
                    index += 1
                top[str(bit)] = op
            self._instructions[mn] = self._merge(existing, top)

    def _merge(self, target, source):
        return source if target is None else {**target, **source}

    def _load_ins_detail(self) -> dict:
        """
        Loads the LR35902 instruction set from the JSON
        file located in the same directory as this script.
        """
        filedir = os.path.realpath(
            os.path.join(os.getcwd(),
                         os.path.dirname(__file__)))
        json_filename = f'{filedir}/gbz80.minified.json'
        if os.path.exists(json_filename):
            fh = open(json_filename)
            return json.load(fh)
        return None

# --------========[ End of InstructionSet class ]========-------- #

###############################################################################


if __name__ == "__main__":
    IS = InstructionSet
    test = IS().is_mnemonic('XOR')
    print(test)
