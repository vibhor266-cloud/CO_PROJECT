import sys

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
    input_path = argv[1]
    output_path = argv[2]
    readable_path = argv[3] if len(argv) > 3 else None
    return input_path, output_path, readable_path

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
