"""
Node Processing.
"""

from enum import IntEnum, auto
from collections import namedtuple
import tempfile
import pprint

import gbasm.core as core
import gbasm.core.constants as const
import gbasm.assembler as asm

EC = core.ExpressionConversion
IS = core.InstructionSet
IP = core.InstructionPointer

TOK = const.TOK
DIR = const.DIR
LBL = const.LBL

class NodeProcessor(object):
    def __init__(self, reader: core.Reader):
        self._reader = reader
        self._line_no = 0
        self._lexer = core.BasicLexer(reader)
        self._code: [asm.CodeNode] = []
        self._bad: [dict] = []
        self._sections: [core.Section] = []

    def process_EQU(self, tokens: list) -> asm.CodeNode:
        """Process an EQU statement. """
        # The tokens should always be multiple since an EQU contains
        # a label followed by the EQU to associate with the label
        if len(tokens) < 2:
            return None
        if tokens[0][DIR] != 'LABEL':
            return None
        if tokens[1][DIR] != 'EQU':
            return None
        result = core.Equate(tokens)
        if result:
            result.parse()
            lbl = core.Label(result.name(), result.value(), constant=True)
            core.Labels().add(lbl)
            return asm.CodeNode(const.NodeType.EQU, lbl, IP().offset_from_base())
        err = core.Error(core.ErrorCode.INVALID_LABEL_NAME,
                    source_file=self._reader.filename,
                    source_line=int(self._reader.line))
        tokens["error"] = err
        # _errors.append(err)
        return asm.CodeNode(const.NodeType.NODE, tokens, 0)

    def process_INSTRUCTION(self, node: dict) -> asm.CodeNode:
        ins = None
        if node is None:
            return None
        ins = core.Instruction(node)
        if ins.parse_result().is_valid():
            offset = IP().offset_from_base()
            IP().move_relative(len(ins.machine_code()))
            return asm.CodeNode(const.NodeType.INST, ins, offset)
        # Instruction is not valid. This could mean either it really is
        # invalid (typo, wrong argument, etc) or that it has a label. To
        # get started, just check to make sure the mnemonic is at least
        # valid.
        offset = IP().offset_from_base()
        if ins.parse_result().mnemonic_error() is None:
            ins2 = asm.Resolver().resolve_instruction(ins, IP().location)
            if ins2 and ins2.is_valid():
                IP().move_relative(len(ins2.machine_code()))
                return asm.CodeNode(const.NodeType.INST, ins2, offset)
        if ins and ins.is_valid():
            IP().move_relative(len(ins.machine_code()))
            return asm.CodeNode(const.NodeType.INST, ins, offset)
        return asm.CodeNode(const.NodeType.NODE, node, offset)  # Error, return the errant node

    def process_LABEL(self, node: dict, value=None) -> asm.CodeNode:
        if not node:
            return None
        if node[DIR] != LBL:
            return None
        clean = node[TOK].strip("()")
        existing = core.Labels()[clean]
        if existing:
            return None
        loc = value
        if not value:
            loc = IP().location
        label = core.Label(clean, loc)
        return asm.CodeNode(const.NodeType.LBL, label, IP().offset_from_base())

    def process_SECTION(self, tokens: dict) -> asm.CodeNode:
        if not tokens or (tokens and tokens[0] != const.SEC):
            return None
        if len(tokens) < 3:
            return None
        try:
            section = self._find_section(' '.join(tokens))
        except core.ParserException:
            return None
        if section is None:  # not found, create a new one.
            secn = core.Section(tokens)
            # print("Processing SECTION")
            self._sections.append(secn)
            num_addr, _ = secn.address_range()
            str_addr = EC().expression_from_value(num_addr,
                                                  "$$")  # 16-bit hex value
            IP().base_address = str_addr

            return secn

    def process_STORAGE(self, node: dict) -> asm.CodeNode:
        if not node:
            return None
        offset = IP().offset_from_base()
        sto = core.Storage(node)
        # print(f"Processing Storage type {sto.storage_type()}")
        # print(f"Storage len = {len(sto)}")
        return asm.CodeNode(const.NodeType.STOR, sto, offset)

    def process_node(self, node: dict) -> [asm.CodeNode]:
        nodes: [asm.CodeNode] = []
        if not core.is_node_valid(node):
            self._bad.append(node)
            return None
        if core.is_compound_node(node):
            # The MULTIPLE case is when a LABEL is on the same line as some
            # other data like an instruction. In some cases this is common
            # like an EQU that is supposed to contain both a LABEL and a
            # value or less common like a LABEL on the same line as an
            # INSTRUCTION.
            multi = self.process_compound_node(node)
            if not multi:
                nodes.append(asm.CodeNode(const.NodeType.NODE, node, IP().offset_from_base()))
            else:
                nodes.extend(multi)
            return nodes
        if node[DIR] == const.SEC:
            sec = self.process_SECTION(node[TOK])
            if sec is None:
                msg = f"Error in parsing section directive. "\
                    "{self.filename}:{self._line_no}"
                err = core.Error(core.ErrorCode.INVALID_SECTION_POSITION,
                            supplimental=msg,
                            source_line=self._line_no)
                node["error"] = err
                nodes.append(asm.CodeNode(const.NodeType.NODE, node, 0))
            else:
                # address = sec.address_range()
                # nodes.append(asm.CodeNode(SEC, sec, address.start))
                nodes.append(asm.CodeNode(const.NodeType.SEC, sec, 0))
            return nodes
        # Just check for a label on it's own line.
        elif node[DIR] == LBL:
            label = self.process_LABEL(node)
            core.Labels().add(label.code_obj)
            nodes.append(label)
        # Lastly, if not any of the above, it _might_be an instruction
        elif node[DIR] == const.INST:
            ins = self.process_INSTRUCTION(node)
            if ins:
                nodes.append(ins)
            else:
                nodes.append(asm.CodeNode(const.NodeType.NODE, node, IP().offset_from_base()))
        return nodes

    def process_compound_node(self, node: dict) -> [asm.CodeNode]:
        tok_list = node[TOK]
        nodes: [asm.CodeNode] = []
        if len(tok_list) < 2:
            # err = Error(ErrorCode.INVALID_DECLARATION,
            #             source_line=self._line_no)
            return None
        # Record a label unless it's an equate. The equate object (which is
        # similar to a label) handles the storage of both.
        if tok_list[0][DIR] == LBL and \
            tok_list[1][DIR] != const.EQU:
            clean = tok_list[0][TOK].strip("()")
            existing = core.Labels()[clean]
            if not existing:
                label = self.process_LABEL(tok_list[0])
                core.Labels().add(label.code_obj)
            else:
                label = asm.CodeNode(const.NodeType.LBL, existing, IP().offset_from_base())
            nodes.append(label)
        # Equate has it's own required label. It's not a standard label
        # in that it can't start with a '.' or end with a ':'
        if tok_list[1][DIR] == const.EQU:
            equ = self.process_EQU(node[TOK])
            nodes.append(equ)
        # An instruction is allowed to be on the same line as a label.
        elif tok_list[1][DIR] == const.INST:
            ins = self.process_INSTRUCTION(tok_list[1])
            nodes.append(ins)
        # Storage values can be associated with a label. The label
        # then can be used almost like an EQU label.
        elif tok_list[1][DIR] == const.STOR:
            storage = self.process_STORAGE(tok_list[1])
            if storage:

                IP().move_location_relative(len(storage.code_obj))
                nodes.append(storage)
                return nodes
        else:
            nodes.append(asm.CodeNode(const.NodeType.NODE, node, IP().offset_from_base()))
        return nodes

    def _find_section(self, line: str) -> core.Section:
        try:
            section = core.Section(line)
        except core.ParserException:
            fname = self._reader.filename()
            msg = f"Parser exception occured {fname}:{self._line_no}"
            print(msg)
            raise core.ParserException(msg, line_number=self._line_no)
        else:
            if section:
                for _, val in enumerate(self._sections):
                    if val.name() == section.name():
                        return section
            return None

