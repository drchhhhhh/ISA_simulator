class RegisterFile:
    """Simulates a 32-register file with 32-bit width."""
    
    def __init__(self):
        # Initialize 32 general-purpose registers (R0-R31)
        self.registers = [0] * 32
        
        # Special registers
        self.pc = 0  # Program Counter
        
        # Status flags
        self.zero_flag = False
        self.negative_flag = False
        self.carry_flag = False
        self.overflow_flag = False
    
    def read(self, reg_num):
        """Read value from specified register."""
        if 0 <= reg_num < 32:
            return self.registers[reg_num]
        else:
            raise ValueError(f"Invalid register number: {reg_num}")
    
    def write(self, reg_num, value):
        """Write value to specified register."""
        if 0 <= reg_num < 32:
            # Ensure value is 32-bit
            self.registers[reg_num] = value & 0xFFFFFFFF
        else:
            raise ValueError(f"Invalid register number: {reg_num}")
    
    def update_flags(self, result):
        """Update status flags based on ALU result."""
        # Zero flag
        self.zero_flag = (result == 0)
        
        # Negative flag
        self.negative_flag = ((result >> 31) & 1) == 1
        
        # Note: Carry and overflow flags would be updated by specific operations
        # that can generate carries or overflows
    
    def dump_registers(self):
        """Print the current state of all registers."""
        for i in range(32):
            print(f"R{i}: {self.registers[i]} (0x{self.registers[i]:08x})")
        
        print(f"PC: {self.pc} (0x{self.pc:08x})")
        print(f"Flags: Z={int(self.zero_flag)} N={int(self.negative_flag)} "
              f"C={int(self.carry_flag)} V={int(self.overflow_flag)}")