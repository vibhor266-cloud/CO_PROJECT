I_type_decode = {
    ("000", "0010011"): "addi",
    ("011", "0010011"): "sltiu",
    ("000", "1100111"): "jalr",
    ("010", "0000011"): "lw",
}

S_type_decode = {
    ("010", "0100011"): "sw",
}

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
