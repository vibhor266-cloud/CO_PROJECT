#!/usr/bin/env python3
"""Assembler implementation compatible with the CO grader interface."""

import sys
from typing import List, Optional


Register_Encoding = {
    "zero": "00000",
    "ra": "00001",
    "sp": "00010",
    "gp": "00011",
    "tp": "00100",
    "t0": "00101",
    "t1": "00110",
    "t2": "00111",
    "s0": "01000",
    "s1": "01001",
    "a0": "01010",
    "a1": "01011",
    "a2": "01100",
    "a3": "01101",
    "a4": "01110",
    "a5": "01111",
    "a6": "10000",
    "a7": "10001",
    "s2": "10010",
    "s3": "10011",
    "s4": "10100",
    "s5": "10101",
    "s6": "10110",
    "s7": "10111",
    "s8": "11000",
    "s9": "11001",
    "s10": "11010",
    "s11": "11011",
    "t3": "11100",
    "t4": "11101",
    "t5": "11110",
    "t6": "11111",
}

for i in range(32):
    Register_Encoding[f"x{i}"] = format(i, "05b")


R_type_registor = {
    "add": ("0000000", "000"),
    "sub": ("0100000", "000"),
    "sll": ("0000000", "001"),
    "slt": ("0000000", "010"),
    "sltu": ("0000000", "011"),
    "xor": ("0000000", "100"),
    "srl": ("0000000", "101"),
    "or": ("0000000", "110"),
    "and": ("0000000", "111"),
}

I_type_register = {
    "addi": ("000", "0010011"),
    "sltiu": ("011", "0010011"),
    "jalr": ("000", "1100111"),
    "lw": ("010", "0000011"),
}

S_type_register = {
    "sw": ("010", "0100011"),
}

U_type_register = {
    "lui": "0110111",
    "auipc": "0010111",
}

B_type_register = {
    "beq": "000",
    "bne": "001",
    "blt": "100",
    "bge": "101",
    "bltu": "110",
    "bgeu": "111",
}

J_type_register = {
    "jal": "1101111",
}

def is_valid_label(label: str) -> bool:
    if not label:
        return False
    if not label[0].isalpha():
        return False
    for ch in label[1:]:
        if not (ch.isalnum() or ch == "_"):
            return False
    return True


def parse_args(argv: List[str]) -> tuple[str, str, Optional[str]]:
    if len(argv) < 3:
        print(
            "Usage: python3 Assembler.py <input_assembly_path> <output_machine_code_path> [output_readable_path]",
            file=sys.stderr,
        )
        sys.exit(1)
    input_path = argv[1]
    output_path = argv[2]
    readable_path = argv[3] if len(argv) > 3 else None
    return input_path, output_path, readable_path


def read_assembly_lines(input_path: str) -> List[str]:
    with open(input_path, "r", encoding="utf-8") as f:
        return f.readlines()


def write_output_lines(path: str, lines: List[str]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        if lines:
            f.write("\n".join(lines))
            f.write("\n")


def write_readable_output(path: str, assembly_lines: List[str], machine_lines: List[str]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write("Input assembly lines:\n")
        for line in assembly_lines:
            f.write(line.rstrip("\n") + "\n")
        f.write("\nGenerated machine lines:\n")
        for line in machine_lines:
            f.write(line + "\n")


def parse_int(token: str) -> int:
    try:
        return int(token, 0)
    except ValueError as exc:
        raise ValueError(f"Invalid immediate: {token}") from exc


def parse_register(token: str) -> str:
    reg = token.strip()
    if reg not in Register_Encoding:
        raise ValueError(f"Invalid register: {token}")
    return reg


def require_signed_range(value: int, bits: int, field_name: str) -> None:
    low = -(1 << (bits - 1))
    high = (1 << (bits - 1)) - 1
    if value < low or value > high:
        raise ValueError(f"{field_name} out of range for {bits}-bit signed immediate: {value}")


def encode_r(inst: str, rd: str, rs1: str, rs2: str) -> str:
    funct7, funct3 = R_type_registor[inst]
    return funct7 + Register_Encoding[rs2] + Register_Encoding[rs1] + funct3 + Register_Encoding[rd] + "0110011"


def encode_i(inst: str, rd: str, rs1: str, imm: int) -> str:
    funct3, opcode_i = I_type_register[inst]
    imm_bin = format(imm & 0xFFF, "012b")
    return imm_bin + Register_Encoding[rs1] + funct3 + Register_Encoding[rd] + opcode_i


def encode_s(inst: str, rs2: str, rs1: str, imm: int) -> str:
    funct3, opcode_s = S_type_register[inst]
    imm_bin = format(imm & 0xFFF, "012b")
    return imm_bin[:7] + Register_Encoding[rs2] + Register_Encoding[rs1] + funct3 + imm_bin[7:] + opcode_s


def encode_b(inst: str, rs1: str, rs2: str, imm: int) -> str:
    imm_bin = format(imm & 0x1FFF, "013b")
    imm12 = imm_bin[0]
    imm10_5 = imm_bin[2:8]
    imm4_1 = imm_bin[8:12]
    imm11 = imm_bin[1]
    return imm12 + imm10_5 + Register_Encoding[rs2] + Register_Encoding[rs1] + B_type_register[inst] + imm4_1 + imm11 + "1100011"


def encode_u(inst: str, rd: str, imm: int) -> str:
    imm_bin = format(imm & 0xFFFFF, "020b")
    return imm_bin + Register_Encoding[rd] + U_type_register[inst]


def encode_j(inst: str, rd: str, imm: int) -> str:
    imm_bin = format(imm & 0x1FFFFF, "021b")
    imm20 = imm_bin[0]
    imm10_1 = imm_bin[10:20]
    imm11 = imm_bin[9]
    imm19_12 = imm_bin[1:9]
    return imm20 + imm10_1 + imm11 + imm19_12 + Register_Encoding[rd] + J_type_register[inst]


def normalize_source_line(raw: str) -> str:
    return raw.split("#", 1)[0].strip()


def parse_labels_and_instructions(assembly_lines: List[str]):
    labels = {}
    instructions = []
    pc = 0

    for idx, raw in enumerate(assembly_lines, start=1):
        line = normalize_source_line(raw)
        if not line:
            continue

        rest = line
        while ":" in rest:
            if rest.startswith(":"):
                raise ValueError(f"Error at line {idx}: Empty label")
            label_part, trailing = rest.split(":", 1)
            label = label_part.strip()

            if " " in label_part or "\t" in label_part:
                raise ValueError(f"Error at line {idx}: Label must be at instruction start with no spaces before ':'")
            if not is_valid_label(label):
                raise ValueError(f"Error at line {idx}: Invalid label name: {label}")
            if label in labels:
                raise ValueError(f"Error at line {idx}: Duplicate label: {label}")

            labels[label] = pc
            rest = trailing.strip()
            if not rest:
                break

        if rest:
            instructions.append((idx, pc, rest))
            pc += 4

    return labels, instructions


def parse_memory_operand(token: str, line_no: int) -> tuple[int, str]:
    token = token.strip()
    if token.count("(") != 1 or token.count(")") != 1 or not token.endswith(")"):
        raise ValueError(f"Error at line {line_no}: Invalid memory operand: {token}")
    left = token.find("(")
    imm_text = token[:left].strip()
    reg_text = token[left + 1 : -1].strip()
    if not imm_text or not reg_text or "," in reg_text or " " in reg_text or "\t" in reg_text:
        raise ValueError(f"Error at line {line_no}: Invalid memory operand: {token}")
    imm = parse_int(imm_text)
    rs1 = parse_register(reg_text)
    return imm, rs1


def resolve_branch_or_jump_target(token: str, labels: dict[str, int], pc: int, line_no: int) -> int:
    if is_valid_label(token):
        if token not in labels:
            raise ValueError(f"Error at line {line_no}: Undefined label: {token}")
        return labels[token] - pc
    return parse_int(token)


def is_virtual_halt(inst: str, operands: List[str]) -> bool:
    if inst != "beq" or len(operands) != 3:
        return False
    try:
        rs1 = parse_register(operands[0])
        rs2 = parse_register(operands[1])
        imm = parse_int(operands[2])
    except ValueError:
        return False
    return rs1 == "zero" and rs2 == "zero" and imm == 0


def assemble(assembly_lines: List[str]) -> List[str]:
    labels, instructions = parse_labels_and_instructions(assembly_lines)
    machine_lines: List[str] = []
    virtual_halt_line: Optional[int] = None

    for idx, parsed in enumerate(instructions):
        line_no, pc, normalized = parsed
        pieces = [p.strip() for p in normalized.replace("\t", " ").split(None, 1)]
        if not pieces:
            continue
        inst = pieces[0]
        operand_text = pieces[1] if len(pieces) > 1 else ""
        operands = [x.strip() for x in operand_text.split(",")] if operand_text else []

        if is_virtual_halt(inst, operands):
            virtual_halt_line = line_no

        if inst in R_type_registor:
            if len(operands) != 3:
                raise ValueError(f"Error at line {parsed.line_no}: R-type needs 3 operands")
            rd = parse_register(operands[0])
            rs1 = parse_register(operands[1])
            rs2 = parse_register(operands[2])
            machine_lines.append(encode_r(inst, rd, rs1, rs2))
            continue

        if inst in I_type_register:
            if inst == "lw":
                if len(operands) != 2:
                    raise ValueError(f"Error at line {line_no}: lw needs 2 operands")
                rd = parse_register(operands[0])
                imm, rs1 = parse_memory_operand(operands[1], line_no)
                require_signed_range(imm, 12, "Immediate")
                machine_lines.append(encode_i(inst, rd, rs1, imm))
            else:
                if len(operands) != 3:
                    raise ValueError(f"Error at line {line_no}: {inst} needs 3 operands")
                rd = parse_register(operands[0])
                rs1 = parse_register(operands[1])
                imm = parse_int(operands[2])
                require_signed_range(imm, 12, "Immediate")
                machine_lines.append(encode_i(inst, rd, rs1, imm))
            continue

        if inst in S_type_register:
            if len(operands) != 2:
                raise ValueError(f"Error at line {line_no}: sw needs 2 operands")
            rs2 = parse_register(operands[0])
            imm, rs1 = parse_memory_operand(operands[1], line_no)
            require_signed_range(imm, 12, "Immediate")
            machine_lines.append(encode_s(inst, rs2, rs1, imm))
            continue

        if inst in B_type_register:
            if len(operands) != 3:
                raise ValueError(f"Error at line {line_no}: {inst} needs 3 operands")
            rs1 = parse_register(operands[0])
            rs2 = parse_register(operands[1])
            imm = resolve_branch_or_jump_target(operands[2], labels, pc, line_no)
            if imm % 2 != 0:
                raise ValueError(f"Error at line {line_no}: Branch immediate must be 2-byte aligned")
            if imm < -4096 or imm > 4094:
                raise ValueError(f"Error at line {line_no}: Branch immediate out of range: {imm}")
            machine_lines.append(encode_b(inst, rs1, rs2, imm))
            continue

        if inst in U_type_register:
            if len(operands) != 2:
                raise ValueError(f"Error at line {line_no}: {inst} needs 2 operands")
            rd = parse_register(operands[0])
            imm = parse_int(operands[1])
            require_signed_range(imm, 20, "Immediate")
            machine_lines.append(encode_u(inst, rd, imm))
            continue

        if inst in J_type_register:
            if len(operands) != 2:
                raise ValueError(f"Error at line {line_no}: jal needs 2 operands")
            rd = parse_register(operands[0])
            imm = resolve_branch_or_jump_target(operands[1], labels, pc, line_no)
            if imm % 2 != 0:
                raise ValueError(f"Error at line {line_no}: Jump immediate must be 2-byte aligned")
            if imm < -1048576 or imm > 1048574:
                raise ValueError(f"Error at line {line_no}: Jump immediate out of range: {imm}")
            machine_lines.append(encode_j(inst, rd, imm))
            continue

        raise ValueError(f"Error at line {line_no}: Unsupported instruction: {inst}")

    if virtual_halt_line is None:
        raise ValueError("Error: Missing Virtual Halt instruction (beq zero,zero,0)")

    return machine_lines


def main() -> None:
    input_path, output_path, readable_path = parse_args(sys.argv)
    assembly_lines = read_assembly_lines(input_path)
    machine_lines: List[str] = []

    try:
        machine_lines = assemble(assembly_lines)
    except ValueError as err:
        print(str(err))
        write_output_lines(output_path, [])
        if readable_path is not None:
            write_readable_output(readable_path, assembly_lines, [])
        return

    write_output_lines(output_path, machine_lines)
    if readable_path is not None:
        write_readable_output(readable_path, assembly_lines, machine_lines)


if __name__ == "__main__":
    main()
