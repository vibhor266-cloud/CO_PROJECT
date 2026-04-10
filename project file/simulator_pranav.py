U_type_decode = {
    "0110111": "lui",
    "0010111": "auipc",
}

class SimulationRuntimeError(ValueError):
    def __init__(self, message: str, partial_output: list[str]):
        super().__init__(message)
        self.partial_output = partial_output

def validate_binary_lines(binary_lines: list[str]) -> None:
    for line_no, line in enumerate(binary_lines, start=1):
        if len(line) != 32 or any(ch not in "01" for ch in line):
            raise ValueError(f"Error at line {line_no}: Invalid 32-bit binary instruction")

if "00000000000000000000000001100011" not in binary_lines:
    raise SimulationRuntimeError("Error: Missing Virtual Halt instruction (beq zero,zero,0)", output)

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

if instr == "00000000000000000000000001100011":
    halt_executed = True
    break

if not halt_executed:
    raise SimulationRuntimeError("Error: Program terminated without executing Virtual Halt instruction", output)

for i in range(32):
    addr = 0x00010000 + i * 4
    val = memory.get(addr, 0)
    output.append(f"0x{addr:08X}:{get_reg_bin(val)}")