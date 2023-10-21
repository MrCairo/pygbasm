SECTION "NewSection", WRAM0[$C100]

IMAGES    EQU $10
BIGVAL    EQU $C020

.program_start:
    ld B, $16 ; This is a comment
    ld BC, $FFD2
    ld a, IMAGES
    LD (BC), A
    JR .program_start
    LD (BIGVAL), A
    ret
