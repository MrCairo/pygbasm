
import sys, os
from gbasm.conversions import ExpressionConversion as EC

def _join_parens(line) -> str:
    new_str = ""
    paren = 0
    for c in line:
        if c == " " and paren > 0:
            continue
        if c in "([{":
            paren += 1
        elif c in ")]}":
            paren -= 1
        paren = max(0, paren) # If Negative set to 0
        new_str += c
    return new_str

def special_split(text) -> list:
    clean = text
    _split = None
    if "(HL+)" in clean or "(HL-)" in clean:
        return None
    if "+" in clean:
        _tmp = clean.split("+")
        if len(_tmp) == 2:
            _split = [_tmp[0], "+", _tmp[1]]
    return _split

def is_arg_inside_parens(arg):
    if arg is not None:
        return arg.startswith("(") and arg.endswith(")")
    return False

def _int_to_z80binary(dec_val, little_endian=True, bits=8) -> bytearray:
    """
    Converts the decimal value to binary format.
    Args:
    little_endian -- Default True, otherwise data is stored as hi, lo.
    bits -- The number of bits to include. Normally this is defined by the
            value. So, a value of $10 can be forced to be $0010 if bits=16.
            Or, a value of $ffd2 can be forced to $d2 if bits=8.
    """
    if dec_val < 0 or dec_val > 65535:
        return None
    ba = bytearray()
    hexi = f"%04x" % dec_val
    low = "0x" + hexi[2:]  # 0xffd2 == 0xd2
    high = "0x" + hexi[0:2]  # 0xffd2 == 0xff
    ba.append(int(low, 16))
    if bits == 16:
        ba.append(int(high, 16))
    # Normally little endian. If not, reverse the order to (hi, lo)
    if not little_endian and len(ba) == 2:
        ba.reverse()
    return ba

def _is_within_parens(value: str) -> bool:
    clean = value.strip()
    return clean.startswith("(") and clean.endswith(")")

def _if_number(num: str, keys: list):
    arg = num
    arg_parens = False
    if is_arg_inside_parens(arg):
        arg = arg.strip("()")
        arg_parens = True
    dec_val = EC().value_from_expression(arg)
    if dec_val:  # Is this an immediate value?
        placeholder = _ph_in_list(keys(),
                                  parens=arg_parens)
        if placeholder:
            bits = 8 if placeholder.find("8") != -1 else 16
            opbytes = _int_to_z80binary(dec_val, bits=bits)
            # If arg has parens then the placeholder must have
            # parens
            if arg_parens != _is_within_parens(placeholder):
                return False
            if self.state.is_arg_in_roamer(placeholder):
                self.state.roam_to_arg()
                self.state.operands["placeholder"] = placeholder
                return True
    else:  # This is just info for an error. arg is NOT a number.
        msg = "The argument is not a numeric value"
        err = Error(ErrorCode.OPERAND_IS_NOT_NUMERIC,
                    supplimental=msg)
        self.state.set_operand_to_val(self.state.arg, err)
    return False

def _ph_in_list(ph_list: list, bits="8", parens=False) -> str:
    """
    For all of the values in the instruction, if any are a placeholder
    then this function will validate and return the placeholder that
    apears in the list. Otherwise, None.
    """
    ph_key = None
    found = False
    regs = {"8": ["r8", "a8", "d8"], "16": ["a16", "d16"]}
    eight = "8" if not parens else "8)"
    sixteen = "16" if not parens else "16)"
    for k in ph_list:
        if k.find(eight) != -1:  # Maybe an 8-bit placeholder key
            ph_key = k
            break
        if k.find(sixteen) != -1:
            ph_key = k
            break
    if ph_key:
        for r in regs["8"]:
            if ph_key.find(r) >= 0:
                found = True
                break
        if not found:
            for r in regs["16"]:
                if ph_key.find(r) >= 0:
                    found = True
                    break
    if found:
        return ph_key
    return None



clean = _join_parens("LD HL, SP+$50")
clean_split = clean.replace(',', ' ').split()

for item in clean_split:
    _plus = special_split(item)
    if _plus:
        print(_plus)

print(f"Clean Split: {clean_split}")
