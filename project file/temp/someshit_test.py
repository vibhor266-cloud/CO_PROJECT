import sys

Register_Decoding = {
    "00000": "zero",
    "00001": "ra",
    "00010": "sp",
    "00011": "gp",
    "00100": "tp",
    "00101": "t0",
    "00110": "t1",
    "00111": "t2",
    "01000": "s0",
    "01001": "s1",
    "01010": "a0",
    "01011": "a1",
    "01100": "a2",
    "01101": "a3",
    "01110": "a4",
    "01111": "a5",
    "10000": "a6",
    "10001": "a7",
    "10010": "s2",
    "10011": "s3",
    "10100": "s4",
    "10101": "s5",
    "10110": "s6",
    "10111": "s7",
    "11000": "s8",
    "11001": "s9",
    "11010": "s10",
    "11011": "s11",
    "11100": "t3",
    "11101": "t4",
    "11110": "t5",
    "11111": "t6",
}
R_type_decode = {
    ("0000000", "000"): "add",
    ("0100000", "000"): "sub",
    ("0000000", "001"): "sll",
    ("0000000", "010"): "slt",
    ("0000000", "011"): "sltu",
    ("0000000", "100"): "xor",
    ("0000000", "101"): "srl",
    ("0000000", "110"): "or",
    ("0000000", "111"): "and",
}

I_type_decode = {
    ("000", "0010011"): "addi",
    ("011", "0010011"): "sltiu",
    ("000", "1100111"): "jalr",
    ("010", "0000011"): "lw",
}

S_type_decode = {
    ("010", "0100011"): "sw",
}

B_type_decode = {
    ("000", "1100011"): "beq",
    ("001", "1100011"): "bne",
    ("100", "1100011"): "blt",
    ("101", "1100011"): "bge",
    ("110", "1100011"): "bltu",
    ("111", "1100011"): "bgeu",
}

U_type_decode = {
    "0110111": "lui",
    "0010111": "auipc",
}

J_type_decode = {
    "1101111": "jal",
}

def parse_args(argv: list[str]) -> tuple[str, str, str | None]:
    if len(argv) < 3:
        print(
            "Usage: python3 Simulator.py <input_assembly_path> <output_machine_code_path> [output_readable_path]",
            file=sys.stderr,
        )
        sys.exit(1)
    input_path = argv[1]
    output_path = argv[2]
    readable_path = argv[3] if len(argv) > 3 else None
    return input_path, output_path, readable_path


def read_assembly_lines(input_path: str) -> list[str]:
    with open(input_path, "r", encoding="utf-8") as f:
        return f.readlines()


def write_output_lines(path: str, lines: list[str]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        if lines:
            f.write(" \n ".join(lines))
            f.write(" \n ")


def write_readable_output(path: str, assembly_lines: list[str], machine_lines: list[str]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(" Input assembly lines:\n")
        
        for line in assembly_lines:
            f.write(line.rstrip("\n") + "\n")
        f.write(" \n Generated machine lines:\n")
        
        for line in machine_lines:
            f.write(line + "\n")


def decode_r(instr: str):
    funct7 = instr[0:7]
    rs2 = instr[7:12]
    rs1 = instr[12:17]
    funct3 = instr[17:20]
    rd = instr[20:25]

    inst = R_type_decode[(funct7, funct3)]

    return f"{inst} {Register_Decoding[rd]}, {Register_Decoding[rs1]}, {Register_Decoding[rs2]}"

def decode_i(instr: str):
    imm = instr[0:12]
    rs1 = instr[12:17]
    funct3 = instr[17:20]
    rd = instr[20:25]
    opcode = instr[25:32]

    inst = I_type_decode[(funct3, opcode)]

    imm_val = int(imm, 2)
    if imm[0] == '1':
        imm_val -= (1 << 12)

    return f"{inst} {Register_Decoding[rd]}, {Register_Decoding[rs1]}, {imm_val}"

def decode_s(instr: str):
    imm1 = instr[0:7]
    rs2 = instr[7:12]
    rs1 = instr[12:17]
    funct3 = instr[17:20]
    imm2 = instr[20:25]
    opcode = instr[25:32]

    inst = S_type_decode[(funct3, opcode)]

    imm = imm1 + imm2
    imm_val = int(imm, 2)
    if imm[0] == '1':
        imm_val -= (1 << 12)

    return f"{inst} {Register_Decoding[rs2]}, {imm_val}({Register_Decoding[rs1]})"

def decode_b(instr: str):
    imm12 = instr[0]
    imm10_5 = instr[1:7]
    rs2 = instr[7:12]
    rs1 = instr[12:17]
    funct3 = instr[17:20]
    imm4_1 = instr[20:24]
    imm11 = instr[24]
    opcode = instr[25:32]

    inst = B_type_decode[(funct3, opcode)]

    imm = imm12 + imm11 + imm10_5 + imm4_1 + "0"
    imm_val = int(imm, 2)
    if imm[0] == '1':
        imm_val -= (1 << 13)

    return f"{inst} {Register_Decoding[rs1]}, {Register_Decoding[rs2]}, {imm_val}"

def decode_u(instr: str):
    imm = instr[0:20]
    rd = instr[20:25]
    opcode = instr[25:32]

    inst = U_type_decode[opcode]

    imm_val = int(imm, 2) << 12

    return f"{inst} {Register_Decoding[rd]}, {imm_val}"

def decode_j(instr: str):
    imm20 = instr[0]
    imm10_1 = instr[1:11]
    imm11 = instr[11]
    imm19_12 = instr[12:20]
    rd = instr[20:25]
    opcode = instr[25:32]

    inst = J_type_decode[opcode]

    imm = imm20 + imm19_12 + imm11 + imm10_1 + "0"
    imm_val = int(imm, 2)
    if imm[0] == '1':
        imm_val -= (1 << 21)

    return f"{inst} {Register_Decoding[rd]}, {imm_val}"

def decode(instr: str):
    opcode = instr[25:32]

    if opcode == "0110011":
        return decode_r(instr)
    elif opcode in ["0010011", "0000011", "1100111"]:
        return decode_i(instr)
    elif opcode == "0100011":
        return decode_s(instr)
    elif opcode == "1100011":
        return decode_b(instr)
    elif opcode in ["0110111", "0010111"]:
        return decode_u(instr)
    elif opcode == "1101111":
        return decode_j(instr)
    else:
        return "Unknown Instruction"

def simulate(binary_lines: list[str]):
    registers = [0] * 32
    memory = {}
    pc = 0

    output = []

    while True:
        # ---- PC safety ----
        if pc // 4 >= len(binary_lines):
            break

        instr = binary_lines[pc // 4]
        opcode = instr[25:32]

        # -------- R-TYPE --------
        if opcode == "0110011":
            funct7 = instr[0:7]
            rs2 = int(instr[7:12], 2)
            rs1 = int(instr[12:17], 2)
            funct3 = instr[17:20]
            rd = int(instr[20:25], 2)

            inst = R_type_decode[(funct7, funct3)]

            if inst == "add":
                registers[rd] = registers[rs1] + registers[rs2]
            elif inst == "sub":
                registers[rd] = registers[rs1] - registers[rs2]
            elif inst == "sll":
                registers[rd] = registers[rs1] << registers[rs2]
            elif inst == "slt":
                registers[rd] = int(registers[rs1] < registers[rs2])
            elif inst == "sltu":
                registers[rd] = int((registers[rs1] & 0xFFFFFFFF) < (registers[rs2] & 0xFFFFFFFF))
            elif inst == "xor":
                registers[rd] = registers[rs1] ^ registers[rs2]
            elif inst == "srl":
                registers[rd] = (registers[rs1] & 0xFFFFFFFF) >> registers[rs2]
            elif inst == "or":
                registers[rd] = registers[rs1] | registers[rs2]
            elif inst == "and":
                registers[rd] = registers[rs1] & registers[rs2]

            pc += 4

        # -------- I-TYPE --------
        elif opcode == "0010011":
            imm = int(instr[0:12], 2)
            if instr[0] == '1':
                imm -= (1 << 12)

            rs1 = int(instr[12:17], 2)
            funct3 = instr[17:20]
            rd = int(instr[20:25], 2)

            inst = I_type_decode[(funct3, opcode)]

            if inst == "addi":
                registers[rd] = registers[rs1] + imm
            elif inst == "sltiu":
                registers[rd] = int((registers[rs1] & 0xFFFFFFFF) < (imm & 0xFFFFFFFF))

            pc += 4

        # -------- LOAD --------
        elif opcode == "0000011":  # lw
            imm = int(instr[0:12], 2)
            if instr[0] == '1':
                imm -= (1 << 12)

            rs1 = int(instr[12:17], 2)
            rd = int(instr[20:25], 2)

            addr = registers[rs1] + imm
            registers[rd] = memory.get(addr, 0)

            pc += 4

        # -------- STORE --------
        elif opcode == "0100011":  # sw
            imm = instr[0:7] + instr[20:25]
            imm_val = int(imm, 2)
            if imm[0] == '1':
                imm_val -= (1 << 12)

            rs2 = int(instr[7:12], 2)
           
def main():
    input_path, output_path, _ = parse_args(sys.argv)

    # ---- Read binary input ----
    with open(input_path, "r") as f:
        binary_lines = [line.strip() for line in f if line.strip()]

    # ---- Run simulator ----
    output_lines = simulate(binary_lines)

    # ---- Write output ----
    with open(output_path, "w") as f:
        for line in output_lines:
            f.write(line + "\n")


if __name__ == "__main__":
    main()