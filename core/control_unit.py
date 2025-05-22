class ControlUnit:
    """Manages instruction decoding and control signal generation."""
    
    # Instruction type ranges
    DATA_PROCESSING_MIN = 0x00
    DATA_PROCESSING_MAX = 0x1F
    MEMORY_ACCESS_MIN = 0x20
    MEMORY_ACCESS_MAX = 0x3F
    CONTROL_FLOW_MIN = 0x40
    CONTROL_FLOW_MAX = 0x5F
    SYSTEM_OPS_MIN = 0x60
    SYSTEM_OPS_MAX = 0x7F
    
    # Example instructions
    ADD = 0x00
    SUB = 0x01
    AND = 0x02
    OR = 0x03
    XOR = 0x04
    SLL = 0x05
    SRL = 0x06
    SRA = 0x07
    SLT = 0x08
    MUL = 0x09
    DIV = 0x0A
    
    # Immediate versions
    ADDI = 0x10
    SUBI = 0x11
    ANDI = 0x12
    ORI = 0x13
    XORI = 0x14
    SLLI = 0x15
    SRLI = 0x16
    SRAI = 0x17
    SLTI = 0x18
    MOVI = 0x19  # Added MOVI instruction
    
    # Register move
    MOV = 0x1F
    
    # Memory access
    LOAD = 0x20
    STORE = 0x21
    PUSH = 0x22
    POP = 0x23
    
    # Control flow
    JMP = 0x40
    BEQ = 0x41  # Branch if equal (zero flag set)
    BNE = 0x42  # Branch if not equal (zero flag clear)
    BLT = 0x43  # Branch if less than (negative flag set)
    BGE = 0x44  # Branch if greater or equal (negative flag clear)
    CALL = 0x45
    RET = 0x46
    
    # System operations
    HALT = 0x60
    IO_READ = 0x61
    IO_WRITE = 0x62
    
    def __init__(self):
        self.halt_flag = False
        self.halt_in_pipeline = False  # New flag to track HALT instruction
        # Control signals
        self.reg_write = False
        self.mem_read = False
        self.mem_write = False
        self.alu_src = False
        self.branch = False
        self.jump = False
        self.mem_to_reg = False

    def decode(self, instruction):
        opcode = (instruction >> 24) & 0xFF
        dest_reg = (instruction >> 16) & 0xFF
        src1_reg = (instruction >> 8) & 0xFF
        src2_reg = instruction & 0xFF
        immediate = instruction & 0xFFFF

        if opcode in (self.BEQ, self.BNE, self.BLT, self.BGE):
            immediate = instruction & 0xFF
            if immediate & 0x80:
                immediate |= 0xFFFFFF00
            src2_reg = (instruction >> 3) & 0x1F
        elif opcode in (self.JMP, self.CALL, self.PUSH, self.POP,
                        self.ADDI, self.SUBI, self.ANDI, self.ORI, self.XORI,
                        self.SLLI, self.SRLI, self.SRAI, self.SLTI,
                        self.MOVI, self.LOAD, self.STORE, self.IO_READ, self.IO_WRITE):
            immediate = instruction & 0xFF
            if immediate & 0x80:
                immediate |= 0xFFFFFF00
        else:
            if immediate & 0x8000:
                immediate |= 0xFFFF0000

        instr_type = self._get_instruction_type(opcode)
        self._reset_control_signals()

        if instr_type == "DATA_PROCESSING":
            self.reg_write = True
            if 0x10 <= opcode <= 0x19:
                self.alu_src = True
        elif instr_type == "MEMORY_ACCESS":
            if opcode in (self.LOAD, self.POP):
                self.mem_read = True
                self.reg_write = True
                self.mem_to_reg = True
                self.alu_src = True
            elif opcode in (self.STORE, self.PUSH):
                self.mem_write = True
                self.alu_src = True
        elif instr_type == "CONTROL_FLOW":
            if opcode in (self.JMP, self.CALL):
                self.jump = True
            elif opcode in (self.BEQ, self.BNE, self.BLT, self.BGE):
                self.branch = True
        elif instr_type == "SYSTEM_OPS":
            if opcode == self.HALT:
                self.halt_in_pipeline = True  # Set HALT tracking flag
            elif opcode == self.IO_READ:
                self.mem_read = True
                self.reg_write = True
            elif opcode == self.IO_WRITE:
                self.mem_write = True

        return {
            "opcode": opcode,
            "dest_reg": dest_reg,
            "src1_reg": src1_reg,
            "src2_reg": src2_reg,
            "immediate": immediate,
            "type": instr_type
        }

    
    def _get_instruction_type(self, opcode):
        """Determine instruction type from opcode."""
        if self.DATA_PROCESSING_MIN <= opcode <= self.DATA_PROCESSING_MAX:
            return "DATA_PROCESSING"
        elif self.MEMORY_ACCESS_MIN <= opcode <= self.MEMORY_ACCESS_MAX:
            return "MEMORY_ACCESS"
        elif self.CONTROL_FLOW_MIN <= opcode <= self.CONTROL_FLOW_MAX:
            return "CONTROL_FLOW"
        elif self.SYSTEM_OPS_MIN <= opcode <= self.SYSTEM_OPS_MAX:
            return "SYSTEM_OPS"
        else:
            return "UNKNOWN"
    
    def _reset_control_signals(self):
        """Reset all control signals to default values."""
        self.reg_write = False
        self.mem_read = False
        self.mem_write = False
        self.alu_src = False
        self.branch = False
        self.jump = False
        self.mem_to_reg = False