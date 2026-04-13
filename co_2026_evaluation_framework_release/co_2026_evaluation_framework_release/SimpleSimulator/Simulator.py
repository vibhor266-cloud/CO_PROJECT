import sys
from pathlib import Path

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

class SimulationRuntimeError(ValueError):
    def __init__(self, message: str, partial_output: list[str]):
        super().__init__(message)
        self.partial_output = partial_output

def to_unsigned(val):
    return val & 0xFFFFFFFF

def to_signed(val):
    val = val & 0xFFFFFFFF
    if val & 0x80000000:
        return val - 0x100000000
    return val

def parse_args(argv: list[str]) -> tuple[str, str, str | None]:
    if len(argv) < 3:
        print(
            "Usage: python3 Simulator.py <input_machine_code_path> <output_trace_path> [output_readable_path]",
            file=sys.stderr,
        )
        sys.exit(1)
    input_path = argv[1].strip()
    output_path = argv[2].strip()
    readable_path = argv[3].strip() if len(argv) > 3 else None
    return input_path, output_path, readable_path

def write_output_file(path_str: str | None, lines: list[str]) -> None:
    if not path_str:
        return

    path = Path(path_str)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="\n") as f:
        for line in lines:
            f.write(line + "\n")

def get_reg_bin(val):
    return "0b" + format(val & 0xFFFFFFFF, "032b")

def validate_binary_lines(binary_lines: list[str]) -> None:
    for line_no, line in enumerate(binary_lines, start=1):
        if len(line) != 32 or any(ch not in "01" for ch in line):
            raise ValueError(f"Error at line {line_no}: Invalid 32-bit binary instruction")

def simulate(binary_lines: list[str]):
    registers = [0] * 32
    registers[2] = 0x0000017C
    memory = {} # Address to value (32-bit int)
    pc = 0
    output = []
    halt_executed = False

    if "00000000000000000000000001100011" not in binary_lines:
        raise SimulationRuntimeError("Error: Missing Virtual Halt instruction (beq zero,zero,0)", output)

    while True:
        if pc < 0:
            raise SimulationRuntimeError(f"Error: PC out of bounds: {pc}", output)
        if pc % 4 != 0:
            raise SimulationRuntimeError(f"Error: PC not 4-byte aligned: {pc}", output)

        if pc // 4 >= len(binary_lines):
            break

        instr = binary_lines[pc // 4]
        opcode = instr[25:32]
        
        old_pc = pc
        next_pc = pc + 4
        
        # -------- R-TYPE --------
        if opcode == "0110011":
            funct7 = instr[0:7]
            rs2_idx = int(instr[7:12], 2)
            rs1_idx = int(instr[12:17], 2)
            funct3 = instr[17:20]
            rd_idx = int(instr[20:25], 2)

            inst = R_type_decode.get((funct7, funct3))
            if inst is None:
                raise SimulationRuntimeError(f"Error: Unsupported R-type instruction at PC {old_pc}: {instr}", output)

            if inst == "add":
                registers[rd_idx] = registers[rs1_idx] + registers[rs2_idx]
            elif inst == "sub":
                registers[rd_idx] = registers[rs1_idx] - registers[rs2_idx]
            elif inst == "sll":
                registers[rd_idx] = registers[rs1_idx] << (registers[rs2_idx] & 0x1F)
            elif inst == "slt":
                registers[rd_idx] = 1 if to_signed(registers[rs1_idx]) < to_signed(registers[rs2_idx]) else 0
            elif inst == "sltu":
                registers[rd_idx] = 1 if to_unsigned(registers[rs1_idx]) < to_unsigned(registers[rs2_idx]) else 0
            elif inst == "xor":
                registers[rd_idx] = registers[rs1_idx] ^ registers[rs2_idx]
            elif inst == "srl":
                registers[rd_idx] = to_unsigned(registers[rs1_idx]) >> (registers[rs2_idx] & 0x1F)
            elif inst == "or":
                registers[rd_idx] = registers[rs1_idx] | registers[rs2_idx]
            elif inst == "and":
                registers[rd_idx] = registers[rs1_idx] & registers[rs2_idx]

        # -------- I-TYPE / JALR / LOAD --------
        elif opcode in ["0010011", "0000011", "1100111"]:
            imm_str = instr[0:12]
            imm_val = int(imm_str, 2)
            if imm_str[0] == '1':
                imm_val -= (1 << 12)
            
            rs1_idx = int(instr[12:17], 2)
            funct3 = instr[17:20]
            rd_idx = int(instr[20:25], 2)
            
            inst = I_type_decode.get((funct3, opcode))
            if inst is None:
                raise SimulationRuntimeError(f"Error: Unsupported I-type instruction at PC {old_pc}: {instr}", output)

            if inst == "addi":
                registers[rd_idx] = registers[rs1_idx] + imm_val
            elif inst == "sltiu":
                registers[rd_idx] = 1 if to_unsigned(registers[rs1_idx]) < to_unsigned(imm_val) else 0
            elif inst == "jalr":
                registers[rd_idx] = old_pc + 4
                next_pc = (registers[rs1_idx] + imm_val) & ~1
            elif inst == "lw":
                addr = registers[rs1_idx] + imm_val
                addr_u = to_unsigned(addr)
                if addr % 4 != 0:
                    raise SimulationRuntimeError(
                        f"Error: Invalid memory read at address 0x{addr_u:08X}", output
                    )
                registers[rd_idx] = memory.get(addr, 0)

        # -------- S-TYPE --------
        elif opcode == "0100011":
            imm_str = instr[0:7] + instr[20:25]
            imm_val = int(imm_str, 2)
            if imm_str[0] == '1':
                imm_val -= (1 << 12)
            
            rs2_idx = int(instr[7:12], 2)
            rs1_idx = int(instr[12:17], 2)
            funct3 = instr[17:20]
            inst = S_type_decode.get((funct3, opcode))
            if inst is None:
                raise SimulationRuntimeError(f"Error: Unsupported S-type instruction at PC {old_pc}: {instr}", output)
            
            addr = registers[rs1_idx] + imm_val
            addr_u = to_unsigned(addr)
            if addr % 4 != 0:
                raise SimulationRuntimeError(
                    f"Error: Invalid memory write at address 0x{addr_u:08X}", output
                )
            memory[addr] = registers[rs2_idx]

        # -------- B-TYPE --------
        elif opcode == "1100011":
            imm_str = instr[0] + instr[24] + instr[1:7] + instr[20:24] + "0"
            imm_val = int(imm_str, 2)
            if imm_str[0] == '1':
                imm_val -= (1 << 13)
            
            rs2_idx = int(instr[7:12], 2)
            rs1_idx = int(instr[12:17], 2)
            funct3 = instr[17:20]
            if (funct3, opcode) not in B_type_decode:
                raise SimulationRuntimeError(f"Error: Unsupported B-type instruction at PC {old_pc}: {instr}", output)
            
            take_branch = False
            if funct3 == "000": # beq
                if registers[rs1_idx] == registers[rs2_idx]: take_branch = True
            elif funct3 == "001": # bne
                if registers[rs1_idx] != registers[rs2_idx]: take_branch = True
            elif funct3 == "100": # blt
                if to_signed(registers[rs1_idx]) < to_signed(registers[rs2_idx]): take_branch = True
            elif funct3 == "101": # bge
                if to_signed(registers[rs1_idx]) >= to_signed(registers[rs2_idx]): take_branch = True
            elif funct3 == "110": # bltu
                if to_unsigned(registers[rs1_idx]) < to_unsigned(registers[rs2_idx]): take_branch = True
            elif funct3 == "111": # bgeu
                if to_unsigned(registers[rs1_idx]) >= to_unsigned(registers[rs2_idx]): take_branch = True
            
            if take_branch:
                next_pc = old_pc + imm_val

        # -------- U-TYPE --------
        elif opcode in ["0110111", "0010111"]:
            imm_str = instr[0:20]
            imm_val = int(imm_str, 2) # 20 bits
            
            rd_idx = int(instr[20:25], 2)
            
            if opcode not in U_type_decode:
                raise SimulationRuntimeError(f"Error: Unsupported U-type instruction at PC {old_pc}: {instr}", output)

            if opcode == "0110111": # lui
                registers[rd_idx] = imm_val << 12
            else: # auipc
                registers[rd_idx] = old_pc + (imm_val << 12)

        # -------- J-TYPE --------
        elif opcode == "1101111":
            imm_str = instr[0] + instr[12:20] + instr[11] + instr[1:11] + "0"
            imm_val = int(imm_str, 2)
            if imm_str[0] == '1':
                imm_val -= (1 << 21)
            
            rd_idx = int(instr[20:25], 2)
            registers[rd_idx] = old_pc + 4
            next_pc = old_pc + imm_val
        else:
            raise SimulationRuntimeError(f"Error: Unsupported opcode at PC {old_pc}: {instr}", output)

        # Finalize step
        pc = next_pc
        registers[0] = 0 # zero register always 0
        for i in range(32):
            registers[i] = to_signed(registers[i]) # Keep consistent with signed representation if preferred

        # Output state
        state_parts = [get_reg_bin(pc)] + [get_reg_bin(registers[i]) for i in range(32)]
        output.append(" ".join(state_parts) + " ")
        
        # Virtual Halt check: beq zero, zero, 0
        if instr == "00000000000000000000000001100011":
            halt_executed = True
            break

    if not halt_executed:
        raise SimulationRuntimeError("Error: Program terminated without executing Virtual Halt instruction", output)

    # Memory Dump: 32 words starting at 0x00010000
    for i in range(32):
        addr = 0x00010000 + i * 4
        val = memory.get(addr, 0)
        output.append(f"0x{addr:08X}:{get_reg_bin(val)}")

    return output

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 Simulator.py <input_machine_code_path> <output_trace_path>")
        sys.exit(1)
        
    input_path, output_path, readable_path = parse_args(sys.argv)

    try:
        with open(input_path, "r") as f:
            binary_lines = [line.strip() for line in f if line.strip()]

        validate_binary_lines(binary_lines)
        output_lines = simulate(binary_lines)
        write_output_file(output_path, output_lines)
        write_output_file(readable_path, output_lines)
    except SimulationRuntimeError as err:
        print(str(err))
        write_output_file(output_path, err.partial_output)
        write_output_file(readable_path, err.partial_output)
    except ValueError as err:
        print(str(err))
        write_output_file(output_path, [])
        write_output_file(readable_path, [])

if __name__ == "__main__":
    main()
