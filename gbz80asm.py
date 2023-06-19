"""
Z80 Assembler
"""
import os
os.environ['DMGASM_ROOT'] = os.path.dirname(os.path.realpath(__file__))

# try:
#     imp.find_module('gbasm_dev')
#     from gbasm_dev import set_gbasm_path
#     set_gbasm_path()
# except ImportError:
#     pass

from dmgasm import Assembler

asm = """
SECTION "CoolStuff",WRAM0
CLOUDS_X: DB $FF,$00,$FF,$00,$FF,$00,$FF,$00,$FF,$00,$FF,$00,$FF,$00,$FF,$00
BUILDINGS_X: DS 1
FLOOR_X: DS 1
PARALLAX_DELAY_TIMER: DS 1
FADE_IN_ACTIVE:: DS 1
FADE_STEP: DS 1
ALLOW_PARALLAX:: DS 1
READ_INPUT:: DS 1
START_PLAY:: DS 1

IMAGES    EQU $10
BIGVAL    EQU 65500

SECTION "game", ROMX

.update_game:
    ld A, (HL)
    jr nz, .update_game
    ld HL, BIGVAL   ; should be 0x21 dc ff
    ld HL, SP+$55   ; should be 0xf8 55
    ldhl sp, $6a    ; should be 0xf8 6a
    jr .continue_update_1
    ld A, (HL)
    XOR D
    CP H
    CP L
.continue_update_1:
    CP A
"""

"""
09/18/2019:
    Need to update the Instruction class (maybe) so that if any part of it is
    resolved from a label, that the label or constant is included in the object
    for reference. This will be necessary (possibly) during linking.
"""
assembler = Assembler()
assembler.load_from_buffer(asm)
assembler.parse()

    #for item in _instructions:
    #    print(item)

    # print(f"Equates: {p.equates}")
    # print("--- BEGIN LABELS DUMP ---")
    # for item in Labels().items():
    #    print(item)
    # print("---- END LABELS DUMP ----")

