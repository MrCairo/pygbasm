def twos_comp(val, bits):
    """compute the 2's complement of int value val"""
    if val & (1 << (bits - 1)) != 0:  # if sign bit is set e.g.(80-ff)
        val = val - (1 << bits)       # compute negative value
    return val                        # return positive value as is

print(twos_comp(0x85, 8))
