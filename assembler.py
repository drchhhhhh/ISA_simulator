class Assembler:
    """Assembles assembly code into machine code for the ISA simulator."""
    
    OPCODES = {
        # Data processing instructions
        "ADD": 0x00,
        "SUB": 0x01,
        "AND": 0x02,
        "OR": 0x03,
        "XOR": 0x04,
        "SLL": 0x05,
        "SRL": 0x06,
        "SRA": 0x07,
        "SLT": 0x08,
        "MUL": 0x09,
        "DIV": 0x0A,
        
        # Immediate versions
        "ADDI": 0x10,
        "SUBI": 0x11,
        "ANDI": 0x12,
        "ORI": 0x13,
        "XORI": 0x14,
        "SLLI": 0x15,
        "SRLI": 0x16,
        "SRAI": 0x17,
        "SLTI": 0x18,
        "MOVI": 0x19,
        
        # Register move
        "MOV": 0x1F,
        
        # Memory access instructions
        "LOAD": 0x20,
        "STORE": 0x21,
        "PUSH": 0x22,
        "POP": 0x23,
        
        # Control flow instructions
        "JMP": 0x40,
        "BEQ": 0x41,
        "BNE": 0x42,
        "BLT": 0x43,
        "BGE": 0x44,
        "CALL": 0x45,
        "RET": 0x46,
        
        # System operations
        "HALT": 0x60,
        "IO_READ": 0x61,
        "IO_WRITE": 0x62
    }
    
    def __init__(self):
        self.symbols = {}
        self.address = 0
        self.errors = []
        self.debug = False
    
    def assemble(self, assembly_code):
        self._first_pass(assembly_code)
        machine_code = self._second_pass(assembly_code)
        if self.errors:
            print("Assembly errors:")
            for e in self.errors:
                print(f"  {e}")
            return None
        return machine_code
    
    def _first_pass(self, assembly_code):
        self.address = 0
        self.symbols = {}
        for line in assembly_code.strip().split('\n'):
            if ';' in line:
                line = line[:line.index(';')]
            line = line.strip()
            if not line:
                continue
            if ':' in line:
                label, rest = line.split(':', 1)
                self.symbols[label.strip()] = self.address
                if rest.strip():
                    self.address += 4
            else:
                self.address += 4
        if self.debug:
            print("Symbol table:")
            for k,v in self.symbols.items():
                print(f"  {k}: 0x{v:08X}")
    
    def _second_pass(self, assembly_code):
        instructions = []
        self.address = 0
        self.errors = []
        for line_num, line in enumerate(assembly_code.strip().split('\n'), 1):
            if ';' in line:
                line = line[:line.index(';')]
            line = line.strip()
            if not line:
                continue
            if ':' in line:
                label, rest = line.split(':', 1)
                if not rest.strip():
                    continue
                line = rest.strip()
            try:
                instr = self._parse_instruction(line, line_num)
                if instr is not None:
                    instructions.append(instr)
                    self.address += 4
            except ValueError as e:
                self.errors.append(f"Line {line_num}: {str(e)}")
        return instructions
    
    def _parse_instruction(self, line, line_num):
        parts = line.split()
        if not parts:
            return None
        
        opcode_str = parts[0].upper()
        if opcode_str not in self.OPCODES:
            self.errors.append(f"Line {line_num}: Unknown opcode '{opcode_str}'")
            return None
        
        # Check for control flow instructions that cannot be assembled
        control_flow_instructions = ["JMP", "BEQ", "BNE", "BLT", "BGE", "CALL"]
        if opcode_str in control_flow_instructions:
            self.errors.append(f"Line {line_num}: function {opcode_str} cannot be assembled.")
            return None

        opcode = self.OPCODES[opcode_str]
        dest_reg = src1_reg = src2_reg = 0
        immediate = 0
        
        if opcode_str in ["ADD", "SUB", "AND", "OR", "XOR", "SLL", "SRL", "SRA", "SLT", "MUL", "DIV"]:
            if len(parts) != 4:
                self.errors.append(f"Line {line_num}: Expected 'OP Rd, Rs1, Rs2'")
                return None
            dest_reg = self._parse_register(parts[1].rstrip(','))
            src1_reg = self._parse_register(parts[2].rstrip(','))
            src2_reg = self._parse_register(parts[3])
        
        elif opcode_str in ["ADDI", "SUBI", "ANDI", "ORI", "XORI", "SLLI", "SRLI", "SRAI", "SLTI"]:
            if len(parts) != 4:
                self.errors.append(f"Line {line_num}: Expected 'OP Rd, Rs1, #Imm'")
                return None
            dest_reg = self._parse_register(parts[1].rstrip(','))
            src1_reg = self._parse_register(parts[2].rstrip(','))
            immediate = self._parse_value(parts[3])
        
        elif opcode_str == "MOVI":
            if len(parts) != 3:
                self.errors.append(f"Line {line_num}: Expected 'MOVI Rd, #Imm'")
                return None
            dest_reg = self._parse_register(parts[1].rstrip(','))
            immediate = self._parse_value(parts[2])
            src1_reg = 0
        
        elif opcode_str == "MOV":
            if len(parts) != 3:
                self.errors.append(f"Line {line_num}: Expected 'MOV Rd, Rs'")
                return None
            dest_reg = self._parse_register(parts[1].rstrip(','))
            src1_reg = self._parse_register(parts[2])
            opcode = self.OPCODES["ADD"]
        
        elif opcode_str in ["LOAD", "STORE"]:
            if len(parts) < 3:
                self.errors.append(f"Line {line_num}: Expected 'OP Rd, [Rs1 + Offset]'")
                return None
            dest_reg = self._parse_register(parts[1].rstrip(','))
            addr_expr = ' '.join(parts[2:])
            if not (addr_expr.startswith('[') and addr_expr.endswith(']')):
                self.errors.append(f"Line {line_num}: Memory address must be '[Rs1 + Offset]'")
                return None
            addr_content = addr_expr[1:-1].strip()
            if '+' in addr_content:
                base_reg_str, offset_str = addr_content.split('+', 1)
                src1_reg = self._parse_register(base_reg_str.strip())
                immediate = self._parse_value(offset_str.strip())
            else:
                src1_reg = self._parse_register(addr_content.strip())
                immediate = 0
        
        elif opcode_str in ["PUSH", "POP"]:
            if len(parts) != 2:
                self.errors.append(f"Line {line_num}: Expected 'OP Rd'")
                return None
            dest_reg = self._parse_register(parts[1])
              
        elif opcode_str == "RET":
            pass
        
        elif opcode_str == "HALT":
            pass
        
        elif opcode_str in ["IO_READ", "IO_WRITE"]:
            if len(parts) != 3:
                self.errors.append(f"Line {line_num}: Expected 'OP Rd, Port'")
                return None
            dest_reg = self._parse_register(parts[1].rstrip(','))
            immediate = self._parse_value(parts[2])
        
        # Default encoding for others
        instruction = (opcode << 24) | (dest_reg << 16) | (src1_reg << 8) | src2_reg
        
        if opcode_str in ["ADDI", "SUBI", "ANDI", "ORI", "XORI", "SLLI", "SRLI", "SRAI", "SLTI", "MOVI",
                          "LOAD", "STORE", "PUSH", "POP", "JMP", "CALL", "IO_READ", "IO_WRITE"]:
            instruction = (instruction & 0xFFFFFF00) | (immediate & 0xFF)
        
        if self.debug:
            print(f"Encoded instruction: {opcode_str} -> 0x{instruction:08X}")
        
        return instruction
    
    def _parse_register(self, reg_str):
        reg_str = reg_str.upper()
        if reg_str.startswith('R'):
            try:
                reg_num = int(reg_str[1:])
                if 0 <= reg_num <= 31:
                    return reg_num
            except ValueError:
                pass
        raise ValueError(f"Invalid register: {reg_str}")
    
    def _parse_value(self, value_str):
        value_str = value_str.strip()
        if value_str.startswith('#'):
            return int(value_str[1:])
        if value_str.lower().startswith('0x'):
            return int(value_str, 16)
        if value_str.lower().startswith('0b'):
            return int(value_str[2:], 2)
        try:
            return int(value_str)
        except ValueError:
            raise ValueError(f"Invalid value: {value_str}")
    
    def disassemble(self, instruction):
        opcode = (instruction >> 24) & 0xFF
        dest_reg = (instruction >> 16) & 0xFF
        src1_reg = (instruction >> 8) & 0xFF
        src2_reg = instruction & 0xFF
        
        opcode_name = None
        for name, code in self.OPCODES.items():
            if code == opcode:
                opcode_name = name
                break
        
        if opcode_name is None:
            return f"UNKNOWN (0x{instruction:08X})"
        
        if opcode_name in ["ADD", "SUB", "AND", "OR", "XOR", "SLL", "SRL", "SRA", "SLT", "MUL", "DIV"]:
            return f"{opcode_name} R{dest_reg}, R{src1_reg}, R{src2_reg}"
        
        elif opcode_name in ["ADDI", "SUBI", "ANDI", "ORI", "XORI", "SLLI", "SRLI", "SRAI", "SLTI"]:
            imm = src2_reg
            return f"{opcode_name} R{dest_reg}, R{src1_reg}, #{imm}"
        
        elif opcode_name == "MOVI":
            imm = src2_reg
            return f"{opcode_name} R{dest_reg}, #{imm}"
        
        elif opcode_name == "MOV":
            return f"{opcode_name} R{dest_reg}, R{src1_reg}"
        
        elif opcode_name in ["LOAD", "STORE"]:
            imm = src2_reg
            return f"{opcode_name} R{dest_reg}, [R{src1_reg} + {imm}]"
        
        elif opcode_name in ["PUSH", "POP"]:
            return f"{opcode_name} R{dest_reg}"
        
        elif opcode_name in ["JMP", "CALL"]:
            imm = instruction & 0xFF
            if imm & 0x80:
                imm -= 0x100
            return f"{opcode_name} {imm}"
        
        elif opcode_name in ["BEQ", "BNE", "BLT", "BGE"]:
            imm = instruction & 0xFF
            if imm & 0x80:
                imm -= 0x100
            return f"{opcode_name} R{dest_reg}, R{src1_reg}, {imm}"
        
        elif opcode_name == "RET" or opcode_name == "HALT":
            return opcode_name
        
        elif opcode_name in ["IO_READ", "IO_WRITE"]:
            port = src2_reg
            return f"{opcode_name} R{dest_reg}, {port}"
        
        return f"UNKNOWN (0x{instruction:08X})"
