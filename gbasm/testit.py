
import json


def _components(instruction: str) -> dict:
    """
    Returns an array of values that represent the individual components
    of an instruction. For example 'LD B, (HL)' would result in an array
    like: ['LD', 'B', '(HL)']
    """
    def clean_split(str_in) -> [str]:
        return list(filter(lambda x: len(x), str_in.split(' ')))

    components = []
    args = []

    if instruction and instruction.strip():
        args = instruction.upper().split(',')
        components = clean_split(args[0].strip())
        if len(args) > 1:
            components += clean_split(args[1])
        opcode = components[0]
        del components[0]
    if not components:
        return {"opcode": opcode}
    return {"opcode": opcode, "operands": components}


def _explode(instruction: str) -> dict:
    """
    Returns an array of values that represent the individual components
    of an instruction. For example 'LD B, (HL)' would result in an array
    like: ['LD', 'B', '(HL)']
    """
    def clean_split(str_in) -> [str]:
        return list(filter(lambda x: len(x), str_in.split(' ')))

    components = []
    args = []
    if instruction and instruction.strip():
        args = instruction.upper().split(',')
        components = clean_split(args.pop(0).strip())
        opcode = components.pop(0)
        components += [x for x in args]
    if not components:
        return {"opcode": opcode}
    return {"opcode": opcode, "operands": components}


if __name__ == "__main__":

    x = []
    y = [4]

    y += [i for i in x]
    print(y)

    print(_explode("Nop"))
    print(_explode("LD A, HL"))
    print(_explode("JP $FFD2"))
    print(_explode("LD A, (HL)"))
