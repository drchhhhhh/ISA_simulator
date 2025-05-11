class Assembler:
    """Assembles assembly code into machine code for the ISA simulator."""
    
    # Opcode definitions matching the Control Unit
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
        self.symbols = {}  # Symbol table for labels
        self.address = 0   # Current address for instruction placement
        self.errors = []   # List to track assembly errors
    
    def assemble(self, assembly_code):
        """Assemble the given assembly code into machine code."""
        # First pass: collect labels
        self._first_pass(assembly_code)
        
        # Second pass: generate machine code
        machine_code = self._second_pass(assembly_code)
        
        # Check for errors
        if self.errors:
            print("Assembly errors:")
            for error in self.errors:
                print(f"  {error}")
            return None
        
        return machine_code
    
    def _first_pass(self, assembly_code):
        """First pass collects all labels and their addresses."""
        self.address = 0
        self.symbols = {}
        
        for line in assembly_code.strip().split('\n'):
            # Remove comments
            if ';' in line:
                line = line[:line.index(';')]
            
            line = line.strip()
            if not line:
                continue
            
            # Check for label
            if ':' in line:
                label, rest = line.split(':', 1)
                label = label.strip()
                self.symbols[label] = self.address
                
                # If there's more on this line, it's an instruction
                if rest.strip():
                    self.address += 4
            else:
                # Regular instruction
                self.address += 4
    
    def _second_pass(self, assembly_code):
        """Second pass generates machine code."""
        instructions = []
        self.address = 0
        self.errors = []
        
        for line_num, line in enumerate(assembly_code.strip().split('\n'), 1):
            # Remove comments
            if ';' in line:
                line = line[:line.index(';')]
            
            line = line.strip()
            if not line:
                continue
            
            # Handle labels
            if ':' in line:
                label, rest = line.split(':', 1)
                rest = rest.strip()
                if not rest:  # Label only, no instruction
                    continue
                line = rest  # Process the instruction after the label
            
            try:
                # Parse the instruction
                instruction = self._parse_instruction(line, line_num)
                if instruction is not None:
                    instructions.append(instruction)
                    self.address += 4
            except ValueError as e:
                self.errors.append(f"Line {line_num}: {str(e)}")
        
        return instructions
    
    def _parse_instruction(self, line, line_num):
        """Parse a single instruction line into machine code."""
        parts = line.split()
        if not parts:
            return None
        
        opcode_str = parts[0].upper()
        if opcode_str not in self.OPCODES:
            self.errors.append(f"Line {line_num}: Unknown opcode '{opcode_str}'")
            return None
        
        opcode = self.OPCODES[opcode_str]
        
        # Initialize instruction fields
        dest_reg = 0
        src1_reg = 0
        src2_reg = 0
        immediate = 0
        
        # Parse based on instruction type
        if opcode_str in ["ADD", "SUB", "AND", "OR", "XOR", "SLL", "SRL", "SRA", "SLT", "MUL", "DIV"]:
            # Format: OP Rd, Rs1, Rs2
            if len(parts) != 4:
                self.errors.append(f"Line {line_num}: Expected format 'OP Rd, Rs1, Rs2'")
                return None
            
            dest_reg = self._parse_register(parts[1].rstrip(','))
            src1_reg = self._parse_register(parts[2].rstrip(','))
            src2_reg = self._parse_register(parts[3])
            
        elif opcode_str in ["ADDI", "SUBI", "ANDI", "ORI", "XORI", "SLLI", "SRLI", "SRAI", "SLTI"]:
            # Format: OP Rd, Rs1, #Imm
            if len(parts) != 4:
                self.errors.append(f"Line {line_num}: Expected format 'OP Rd, Rs1, #Imm'")
                return None
            
            dest_reg = self._parse_register(parts[1].rstrip(','))
            src1_reg = self._parse_register(parts[2].rstrip(','))
            immediate = self._parse_value(parts[3])
            
        elif opcode_str == "MOV":
            # Format: MOV Rd, Rs
            if len(parts) != 3:
                self.errors.append(f"Line {line_num}: Expected format 'MOV Rd, Rs'")
                return None
            
            dest_reg = self._parse_register(parts[1].rstrip(','))
            src1_reg = self._parse_register(parts[2])
            # MOV is implemented as ADD Rd, Rs, R0
            opcode = self.OPCODES["ADD"]
            
        elif opcode_str in ["LOAD", "STORE"]:
            # Format: OP Rd, [Rs1 + Offset]
            if len(parts) < 3:
                self.errors.append(f"Line {line_num}: Expected format 'OP Rd, [Rs1 + Offset]'")
                return None
            
            dest_reg = self._parse_register(parts[1].rstrip(','))
            
            # Parse memory address expression [Rs1 + Offset]
            addr_expr = ' '.join(parts[2:])
            if not (addr_expr.startswith('[') and addr_expr.endswith(']')):
                self.errors.append(f"Line {line_num}: Memory address must be in format [Rs1 + Offset]")
                return None
            
            # Extract content between brackets
            addr_content = addr_expr[1:-1].strip()
            
            if '+' in addr_content:
                base_reg_str, offset_str = addr_content.split('+', 1)
                src1_reg = self._parse_register(base_reg_str.strip())
                immediate = self._parse_value(offset_str.strip())
            else:
                src1_reg = self._parse_register(addr_content.strip())
                immediate = 0
            
        elif opcode_str in ["PUSH", "POP"]:
            # Format: OP Rd
            if len(parts) != 2:
                self.errors.append(f"Line {line_num}: Expected format 'OP Rd'")
                return None
            
            dest_reg = self._parse_register(parts[1])
            
        elif opcode_str in ["JMP", "CALL"]:
            # Format: OP Label or OP Offset
            if len(parts) != 2:
                self.errors.append(f"Line {line_num}: Expected format 'OP Label' or 'OP Offset'")
                return None
            
            target = parts[1]
            
            # Check if target is a label
            if target in self.symbols:
                # Calculate relative offset (in words)
                offset = (self.symbols[target] - self.address) >> 2
                immediate = offset & 0xFFFF  # Truncate to 16 bits
            else:
                # Try to parse as immediate value
                try:
                    immediate = self._parse_value(target)
                except ValueError:
                    self.errors.append(f"Line {line_num}: Unknown label '{target}'")
                    return None
            
        elif opcode_str in ["BEQ", "BNE", "BLT", "BGE"]:
            # Format: OP Rs1, Rs2, Label
            if len(parts) != 4:
                self.errors.append(f"Line {line_num}: Expected format 'OP Rs1, Rs2, Label'")
                return None
            
            src1_reg = self._parse_register(parts[1].rstrip(','))
            src2_reg = self._parse_register(parts[2].rstrip(','))
            
            target = parts[3]
            
            # Check if target is a label
            if target in self.symbols:
                # Calculate relative offset (in words)
                offset = (self.symbols[target] - self.address) >> 2
                immediate = offset & 0xFFFF  # Truncate to 16 bits
            else:
                # Try to parse as immediate value
                try:
                    immediate = self._parse_value(target)
                except ValueError:
                    self.errors.append(f"Line {line_num}: Unknown label '{target}'")
                    return None
            
        elif opcode_str == "RET":
            # No operands
            pass
            
        elif opcode_str == "HALT":
            # No operands
            pass
            
        elif opcode_str in ["IO_READ", "IO_WRITE"]:
            # Format: OP Rd, Port
            if len(parts) != 3:
                self.errors.append(f"Line {line_num}: Expected format 'OP Rd, Port'")
                return None
            
            dest_reg = self._parse_register(parts[1].rstrip(','))
            immediate = self._parse_value(parts[2])
        
        # Encode instruction
        # Format: [8-bit opcode][8-bit dest_reg][8-bit src1_reg][8-bit src2_reg]
        instruction = (opcode << 24) | (dest_reg << 16) | (src1_reg << 8) | src2_reg
        
        # For instructions with immediates, the src2_reg field is replaced with the immediate
        if opcode_str in ["ADDI", "SUBI", "ANDI", "ORI", "XORI", "SLLI", "SRLI", "SRAI", "SLTI",
                         "LOAD", "STORE", "PUSH", "POP", "JMP", "CALL", "IO_READ", "IO_WRITE"]:
            # Clear the src2_reg field and set the immediate
            instruction = (instruction & 0xFFFFFF00) | (immediate & 0xFF)
        
        # For branch instructions, we need to store the full 16-bit immediate
        if opcode_str in ["BEQ", "BNE", "BLT", "BGE"]:
            # Clear the lower 16 bits and set the immediate
            instruction = (instruction & 0xFFFF0000) | (immediate & 0xFFFF)
        
        return instruction
    
    def _parse_register(self, reg_str):
        """Parse a register string (R0, R1, etc.) into register number."""
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
        """Parse a value string into an integer."""
        value_str = value_str.strip()
        
        # Handle decimal numbers
        if value_str.startswith('#'):
            return int(value_str[1:])
        
        # Handle hexadecimal numbers
        if value_str.startswith('0X') or value_str.startswith('0x'):
            return int(value_str, 16)
        
        # Handle binary numbers
        if value_str.startswith('0B') or value_str.startswith('0b'):
            return int(value_str[2:], 2)
        
        # Try as decimal
        try:
            return int(value_str)
        except ValueError:
            raise ValueError(f"Invalid value: {value_str}")
    
    def disassemble(self, instruction):
        """Convert a machine code instruction back to assembly."""
        opcode = (instruction >> 24) & 0xFF
        dest_reg = (instruction >> 16) & 0xFF
        src1_reg = (instruction >> 8) & 0xFF
        src2_reg = instruction & 0xFF
        
        # Find opcode name
        opcode_name = None
        for name, code in self.OPCODES.items():
            if code == opcode:
                opcode_name = name
                break
        
        if opcode_name is None:
            return f"UNKNOWN (0x{instruction:08X})"
        
        # Format based on instruction type
        if opcode_name in ["ADD", "SUB", "AND", "OR", "XOR", "SLL", "SRL", "SRA", "SLT", "MUL", "DIV"]:
            return f"{opcode_name} R{dest_reg}, R{src1_reg}, R{src2_reg}"
            
        elif opcode_name in ["ADDI", "SUBI", "ANDI", "ORI", "XORI", "SLLI", "SRLI", "SRAI", "SLTI"]:
            imm = src2_reg
            return f"{opcode_name} R{dest_reg}, R{src1_reg}, #{imm}"
            
        elif opcode_name == "MOV":
            return f"MOV R{dest_reg}, R{src1_reg}"
            
        elif opcode_name in ["LOAD", "STORE"]:
            imm = src2_reg
            return f"{opcode_name} R{dest_reg}, [R{src1_reg} + {imm}]"
            
        elif opcode_name in ["PUSH", "POP"]:
            return f"{opcode_name} R{dest_reg}"
            
        elif opcode_name in ["JMP", "CALL"]:
            imm = instruction & 0xFFFF  # 16-bit immediate
            return f"{opcode_name} {imm}"
            
        elif opcode_name in ["BEQ", "BNE", "BLT", "BGE"]:
            imm = instruction & 0xFFFF  # 16-bit immediate
            return f"{opcode_name} R{dest_reg}, R{src1_reg}, {imm}"
            
        elif opcode_name == "RET" or opcode_name == "HALT":
            return opcode_name
            
        elif opcode_name in ["IO_READ", "IO_WRITE"]:
            port = src2_reg
            return f"{opcode_name} R{dest_reg}, {port}"
            
        return f"UNKNOWN (0x{instruction:08X})"