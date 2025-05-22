class ALU:
    """Arithmetic Logic Unit for performing computations."""
    
    # ALU operation codes
    OP_ADD = 0
    OP_SUB = 1
    OP_AND = 2
    OP_OR = 3
    OP_XOR = 4
    OP_SLL = 5  # Shift left logical
    OP_SRL = 6  # Shift right logical
    OP_SRA = 7  # Shift right arithmetic
    OP_SLT = 8  # Set less than
    OP_MUL = 9  # Multiplication
    OP_DIV = 10 # Division
    OP_MOV = 11 # Move (pass operand2 directly)
    
    def __init__(self, register_file):
        self.reg_file = register_file
    
    def execute(self, op_code, operand1, operand2):
        """Execute the specified ALU operation."""
        result = 0
        
        # Ensure operands are treated as 32-bit unsigned values
        operand1 = operand1 & 0xFFFFFFFF
        operand2 = operand2 & 0xFFFFFFFF
        
        if op_code == self.OP_ADD:
            print(f"ADD: {operand1} + {operand2}")
            result = (operand1 + operand2) & 0xFFFFFFFF
            # Check for carry
            self.reg_file.carry_flag = (operand1 + operand2) > 0xFFFFFFFF
            
        elif op_code == self.OP_SUB:
            print(f"SUB: {operand1} - {operand2}")
            result = (operand1 - operand2) & 0xFFFFFFFF
            # Check for borrow
            self.reg_file.carry_flag = operand1 >= operand2
                
        elif op_code == self.OP_AND:
            result = operand1 & operand2
            print(f"AND: {operand1} & {operand2} == {result}")
            
        elif op_code == self.OP_OR:
            result = operand1 | operand2
            print(f"OR: {operand1} | {operand2} == {result}")
            
        elif op_code == self.OP_XOR:
            result = operand1 ^ operand2
            print(f"XOR: {operand1} ^ {operand2} == {result}")
            
        elif op_code == self.OP_SLL:
            result = operand1 << (operand2 & 0x1F)  # Use only bottom 5 bits for shift
            
        elif op_code == self.OP_SRL:
            result = operand1 >> (operand2 & 0x1F)
            
        elif op_code == self.OP_SRA:
            # Arithmetic shift maintains sign bit
            shift_amount = operand2 & 0x1F
            if (operand1 & 0x80000000) == 0:  # Positive number
                result = operand1 >> shift_amount
            else:  # Negative number
                result = operand1 >> shift_amount
                # Set the high bits to 1
                mask = (1 << shift_amount) - 1
                mask = mask << (32 - shift_amount)
                result |= mask
                
        elif op_code == self.OP_SLT:
            result = 1 if operand1 < operand2 else 0
            
        elif op_code == self.OP_MUL:
            print(f"MUL: {operand1} * {operand2}")
            # Simple multiplication, ignoring overflow
            result = (operand1 * operand2) & 0xFFFFFFFF
            
        elif op_code == self.OP_DIV:
            print(f"DIV: {operand1} / {operand2}")
            # Handle division by zero
            if operand2 == 0:
                print("Warning: Division by zero")
                result = 0
            else:
                # Convert to signed for division if needed
                if operand1 & 0x80000000:  # If negative
                    signed_op1 = -((~operand1 + 1) & 0xFFFFFFFF)
                else:
                    signed_op1 = operand1
                    
                if operand2 & 0x80000000:  # If negative
                    signed_op2 = -((~operand2 + 1) & 0xFFFFFFFF)
                else:
                    signed_op2 = operand2
                    
                # Perform division and convert back to 32-bit
                result = (signed_op1 // signed_op2) & 0xFFFFFFFF
                
        elif op_code == self.OP_MOV:
            # For MOVI, just pass operand2 directly
            result = operand2
            
        else:
            raise ValueError(f"Unknown ALU operation: {op_code}")
        
        # Update flags based on result
        self.reg_file.update_flags(result)
        
        return result & 0xFFFFFFFF  # Ensure 32-bit result