from core.register_file import RegisterFile
from core.memory import Memory
from core.alu import ALU
from core.control_unit import ControlUnit
from core.pipeline_register import PipelineRegister
from assembler import Assembler

class ISASimulator:
    """Main simulator class integrating all components."""
    
    def __init__(self, memory_size=1024*1024, debug=False):
        self.reg_file = RegisterFile()
        self.memory = Memory(memory_size)
        self.alu = ALU(self.reg_file)
        self.control_unit = ControlUnit()
        self.assembler = Assembler()  # Add assembler for disassembly
        
        # Pipeline registers
        self.if_id = PipelineRegister("IF/ID")
        self.id_ex = PipelineRegister("ID/EX")
        self.ex_mem = PipelineRegister("EX/MEM")
        self.mem_wb = PipelineRegister("MEM/WB")
        
        # Pipeline control
        self.stall = False
        self.flush = False
        
        # Performance metrics
        self.cycles = 0
        self.instructions_executed = 0
        self.stall_cycles = 0

        # Debug mode
        self.debug = debug
    
    def load_program(self, instructions, start_address=0):
        """Load program into memory."""
        self.memory.load_program(instructions, start_address)
        self.reg_file.pc = start_address  # Reset PC to start address
    
    def run(self, max_cycles=1000):
        """Run the simulation for specified number of cycles."""
        cycle = 0
        
        while cycle < max_cycles and not self.control_unit.halt_flag:
            # Execute pipeline stages in reverse order
            self._writeback_stage()
            self._memory_stage()
            self._execute_stage()
            self._decode_stage()
            self._fetch_stage()
            
            cycle += 1
            self.cycles += 1
            
            # Print cycle information for debugging
            if self.debug:
                print(f"Cycle {cycle}: PC = {hex(self.reg_file.pc)}")
            
            # Handle hazards
            self._hazard_detection()
            
            # Check for termination
            if self.control_unit.halt_flag:
                if self.debug:
                    print("HALT instruction encountered")
                break
        
        return {
            "cycles": self.cycles,
            "instructions": self.instructions_executed,
            "stalls": self.stall_cycles,
            "ipc": self.instructions_executed / self.cycles if self.cycles > 0 else 0
        }
    
    def step(self):
        """Execute a single cycle of the pipeline."""
        # Execute pipeline stages in reverse order to prevent data overwriting
        self._writeback_stage()
        self._memory_stage()
        self._execute_stage()
        self._decode_stage()
        self._fetch_stage()
        
        self.cycles += 1
        
        # Handle hazards
        self._hazard_detection()
        
        # Debug output to track pipeline state
        if self.debug:
            print(f"--- Cycle {self.cycles} ---")
            print(f"PC: 0x{self.reg_file.pc:08X}")
            print("Pipeline Registers:")
            print(f"IF/ID: {self.if_id.data}")
            print(f"ID/EX: {self.id_ex.data}")
            print(f"EX/MEM: {self.ex_mem.data}")
            print(f"MEM/WB: {self.mem_wb.data}")
            print("Register File:")
            for i in range(8):  # Print first 8 registers
                print(f"R{i}: {self.reg_file.registers[i]} (0x{self.reg_file.registers[i]:08X})")
            print("Flags: Z={} N={} C={} V={}".format(
                int(self.reg_file.zero_flag),
                int(self.reg_file.negative_flag),
                int(self.reg_file.carry_flag),
                int(self.reg_file.overflow_flag)
            ))
            print()
        
        return not self.control_unit.halt_flag
    
    def _fetch_stage(self):
        """Instruction Fetch (IF) stage."""
        if not self.stall:
            # Fetch instruction from memory at PC
            try:
                instruction = self.memory.read_word(self.reg_file.pc)
                
                # Write to IF/ID pipeline register
                self.if_id.write("instruction", instruction)
                self.if_id.write("pc", self.reg_file.pc)
                
                # Increment PC
                self.reg_file.pc += 4
            except ValueError as e:
                if self.debug:
                    print(f"Fetch error: {e}")
                self.control_unit.halt_flag = True
    
    def _decode_stage(self):
        """Instruction Decode (ID) stage."""
        if self.flush:
            self.if_id.clear()
            self.flush = False
            return
        
        instruction = self.if_id.read("instruction")
        if instruction is None:
            return  # Nothing to decode
        
        # Decode instruction
        decoded = self.control_unit.decode(instruction)
        
        # Read register values
        src1_val = self.reg_file.read(decoded["src1_reg"])
        src2_val = self.reg_file.read(decoded["src2_reg"])
        
        # Pass values to ID/EX register
        self.id_ex.write("control", {
            "reg_write": self.control_unit.reg_write,
            "mem_read": self.control_unit.mem_read,
            "mem_write": self.control_unit.mem_write,
            "alu_src": self.control_unit.alu_src,
            "branch": self.control_unit.branch,
            "jump": self.control_unit.jump,
            "mem_to_reg": self.control_unit.mem_to_reg
        })
        
        self.id_ex.write("src1_val", src1_val)
        self.id_ex.write("src2_val", src2_val)
        self.id_ex.write("immediate", decoded["immediate"])
        self.id_ex.write("dest_reg", decoded["dest_reg"])
        self.id_ex.write("src1_reg", decoded["src1_reg"])
        self.id_ex.write("src2_reg", decoded["src2_reg"])
        self.id_ex.write("opcode", decoded["opcode"])
        self.id_ex.write("pc", self.if_id.read("pc"))
    
    def _execute_stage(self):
        """Execute (EX) stage."""
        control = self.id_ex.read("control")
        if control is None:
            return  # Nothing to execute
        
        src1_val = self.id_ex.read("src1_val")
        src2_val = self.id_ex.read("src2_val")
        immediate = self.id_ex.read("immediate")
        opcode = self.id_ex.read("opcode")
        
        # Determine second operand (register or immediate)
        operand2 = immediate if control["alu_src"] else src2_val
        
        # Execute operation (map opcode to ALU operation)
        alu_op = opcode & 0x0F  # Use lower 4 bits for ALU operation
        result = self.alu.execute(alu_op, src1_val, operand2)
        
        # Calculate branch target if needed
        branch_target = None
        if control["branch"] or control["jump"]:
            pc = self.id_ex.read("pc")
            branch_target = pc + (immediate << 2)  # Scale by 4 for byte addressing
        
        # Pass values to EX/MEM register
        self.ex_mem.write("control", control)
        self.ex_mem.write("alu_result", result)
        self.ex_mem.write("src2_val", src2_val)  # For STORE instructions
        self.ex_mem.write("dest_reg", self.id_ex.read("dest_reg"))
        self.ex_mem.write("branch_target", branch_target)
        self.ex_mem.write("opcode", opcode)  # Pass opcode for branch condition checking
        
        # Handle branch decisions
        if control["branch"]:
            take_branch = False
            
            if opcode == self.control_unit.BEQ:
                take_branch = self.reg_file.zero_flag
            elif opcode == self.control_unit.BNE:
                take_branch = not self.reg_file.zero_flag
            elif opcode == self.control_unit.BLT:
                take_branch = self.reg_file.negative_flag
            elif opcode == self.control_unit.BGE:
                take_branch = not self.reg_file.negative_flag
                
            if take_branch and branch_target is not None:
                # Branch taken
                self.reg_file.pc = branch_target
                self.flush = True
                
        elif control["jump"] and branch_target is not None:
            # Unconditional jump
            self.reg_file.pc = branch_target
            self.flush = True
    
    def _memory_stage(self):
        """Memory Access (MEM) stage."""
        control = self.ex_mem.read("control")
        if control is None:
            return  # Nothing to access
        
        alu_result = self.ex_mem.read("alu_result")
        mem_data = None
        
        try:
            if control["mem_read"]:
                # Load operation
                mem_data = self.memory.read_word(alu_result)
            elif control["mem_write"]:
                # Store operation
                self.memory.write_word(alu_result, self.ex_mem.read("src2_val"))
        except ValueError as e:
            if self.debug:
                print(f"Memory access error: {e}")
            self.control_unit.halt_flag = True
        
        # Pass values to MEM/WB register
        self.mem_wb.write("control", control)
        self.mem_wb.write("alu_result", alu_result)
        self.mem_wb.write("mem_data", mem_data)
        self.mem_wb.write("dest_reg", self.ex_mem.read("dest_reg"))
    
    def _writeback_stage(self):
        """Write Back (WB) stage."""
        control = self.mem_wb.read("control")
        if control is None:
            return  # Nothing to write back
        
        if control["reg_write"]:
            dest_reg = self.mem_wb.read("dest_reg")
            
            # Determine write data source
            if control["mem_to_reg"]:
                write_data = self.mem_wb.read("mem_data")
            else:
                write_data = self.mem_wb.read("alu_result")
            
            # Write to register file (skip R0 which is hardwired to 0)
            if dest_reg != 0:
                self.reg_file.write(dest_reg, write_data)
            
            self.instructions_executed += 1
    
    def _hazard_detection(self):
        """Detect and handle data hazards."""
        # Check for data hazards (RAW - Read After Write)
        id_ex_control = self.id_ex.read("control")
        if id_ex_control and id_ex_control.get("mem_read"):
            id_ex_dest = self.id_ex.read("dest_reg")
            if_id_instr = self.if_id.read("instruction")
            
            if if_id_instr is not None:
                # Decode next instruction to check register dependencies
                next_decoded = self.control_unit.decode(if_id_instr)
                
                # Check if next instruction uses the result of current load
                if id_ex_dest in [next_decoded["src1_reg"], next_decoded["src2_reg"]]:
                    # Stall the pipeline
                    self.stall = True
                    self.stall_cycles += 1
                    return
        
        # No hazard detected
        self.stall = False