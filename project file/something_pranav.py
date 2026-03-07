#!/usr/bin/env python3
"""Basic assembler I/O skeleton compatible with the CO grader."""

from __future__ import annotations

import sys
from typing import List, Optional


def parse_args(argv: List[str]) -> tuple[str, str, Optional[str]]:
    """
    Expected by grader:
      python3 Assembler.py <input_assembly_path> <output_machine_code_path> [output_readable_path]
    """
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


def assemble(assembly_lines: List[str]) -> List[str]:
    opcode = "0110011"

    r_type_map = {
        "add":  ("000", "0000000"),
        "sub":  ("000", "0100000"),
        "sll":  ("001", "0000000"),
        "slt":  ("010", "0000000"),
        "sltu": ("011", "0000000"),
        "xor":  ("100", "0000000"),
        "srl":  ("101", "0000000"),
        "sra":  ("101", "0100000"),
        "or":   ("110", "0000000"),
        "and":  ("111", "0000000"),
    }

    u_type_map = {
        "lui": "0110111",
        "auipc": "0010111",
    }

    machine_lines = []

    for line in assembly_lines:
        line = line.split("#")[0].strip()
        if not line:
            continue

        if line == "beq zero, zero, 0":
            machine_lines.append("00000000000000000000000001100011")
            break

        parts = line.replace(",", "").split()
        instr = parts[0]

        if instr in u_type_map:

            if len(parts) < 3:
                raise ValueError("Invalid U-type instruction format")

            rd = parts[1]
            imm = parts[2]

            if not rd.startswith("x"):
                raise ValueError("Invalid register format")

            rd_num = int(rd[1:])
            if rd_num < 0 or rd_num > 31:
                raise ValueError("Register out of range")

            imm_val = int(imm)
            if imm_val < 0 or imm_val > (2**20 - 1):
                raise ValueError("Immediate out of range")

            rd_bin = format(rd_num, "05b")
            imm_bin = format(imm_val, "020b")

            opcode_u = u_type_map[instr]

            binary = imm_bin + rd_bin + opcode_u
            machine_lines.append(binary)

            continue

        if instr not in r_type_map and instr not in u_type_map:
            raise ValueError(f"Unsupported instruction: {instr}")

        if instr in r_type_map:

            if len(parts) < 4:
                raise ValueError("Invalid R-type instruction format")

            if not parts[1].startswith("x") or not parts[2].startswith("x") or not parts[3].startswith("x"):
                raise ValueError("Invalid register format")

            rd = int(parts[1][1:])
            rs1 = int(parts[2][1:])
            rs2 = int(parts[3][1:])

            if rd > 31 or rs1 > 31 or rs2 > 31:
                raise ValueError("Register out of range")

            funct7, funct3 = r_type_map[instr]

            rd_bin = format(rd, "05b")
            rs1_bin = format(rs1, "05b")
            rs2_bin = format(rs2, "05b")

            machine_code = (
                funct7 +
                rs2_bin +
                rs1_bin +
                funct3 +
                rd_bin +
                opcode
            )

            machine_lines.append(machine_code)

    return machine_lines


def write_output_lines(path: str, lines: List[str]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        if lines:
            f.write("\n".join(lines))
            f.write("\n")


def write_readable_output(path: str, assembly_lines: List[str], machine_lines: List[str]) -> None:
    """
    Optional debug/readable file. Grader may pass this path as argv[3].
    """
    with open(path, "w", encoding="utf-8") as f:
        f.write("Input assembly lines:\n")
        for line in assembly_lines:
            f.write(line.rstrip("\n") + "\n")
        f.write("\nGenerated machine lines:\n")
        for line in machine_lines:
            f.write(line + "\n")


def main() -> None:
    input_path, output_path, readable_path = parse_args(sys.argv)
    assembly_lines = read_assembly_lines(input_path)
    machine_lines = assemble(assembly_lines)
    write_output_lines(output_path, machine_lines)

    if readable_path is not None:
        write_readable_output(readable_path, assembly_lines, machine_lines)


if __name__ == "__main__":
    main()