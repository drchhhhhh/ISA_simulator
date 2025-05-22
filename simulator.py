from core.register_file import RegisterFile
from core.memory import Memory
from core.alu import ALU
from core.control_unit import ControlUnit
from core.pipeline_register import PipelineRegister
from assembler import Assembler
from register_debugger import RegisterDebugger

class ISASimulator:
    """Main simulator class integrating all components with register debugging."""
    
    def __init__(self, memory_size=1024*1024, debug=False):
        self.reg_file = RegisterFile()
        self.memory = Memory(memory_size)
        self.alu = ALU(self.reg_file)
        self.instruction_history = {}
        self.all_instructions = {}
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

        self.flush_cycle_count = 0  # Track how many cycles flush has been active
        
        # Track pipeline stages for visualization
        self.pipeline_stages = []  # Track instructions in each stage per cycle
        
        # Register debugger
        self.register_debugger = RegisterDebugger(self)
    
    def load_program(self, instructions, start_address=0):
        """Load program into memory."""
        self.memory.load_program(instructions, start_address)
        self.reg_file.pc = start_address  # Reset PC to start address
        
        # Clear pipeline stages history
        self.pipeline_stages = []
    
    def run(self, max_cycles=1000):
        cycle = 0
        while cycle < max_cycles:
            self.step()
            cycle += 1
            # Check if HALT is in writeback stage
            if self.mem_wb.read("instruction") is not None:
                opcode = (self.mem_wb.read("instruction") >> 24) & 0xFF
                if opcode == self.control_unit.HALT:
                    if self.debug:
                        print("HALT instruction reached writeback stage")
                    self.control_unit.halt_flag = True
                    break
        return {
            "cycles": self.cycles,
            "instructions": self.instructions_executed,
            "stalls": self.stall_cycles,
            "ipc": self.instructions_executed / self.cycles if self.cycles > 0 else 0
        }
    
    def step(self):
        # Start tracking a new cycle
        self.register_debugger.start_cycle(self.cycles)
        
        # Check if HALT has reached writeback - can terminate early
        if self.mem_wb.read("instruction") is not None:
            opcode = (self.mem_wb.read("instruction") >> 24) & 0xFF
            if opcode == self.control_unit.HALT:
                print("HALT instruction reached writeback stage, terminating simulation")
                self.control_unit.halt_flag = True
                return False
        
        current_state = {
            'fetch': self._get_instruction_at_pc(self.reg_file.pc),
            'decode': self.if_id.read("instruction"),
            'execute': self.id_ex.read("instruction"),
            'memory': self.ex_mem.read("instruction"),
            'writeback': self.mem_wb.read("instruction")
        }
        self._writeback_stage()
        self._memory_stage()
        self._execute_stage()
        self._decode_stage()
        self._fetch_stage()
        self.cycles += 1
        self._hazard_detection()
        self.pipeline_stages.append(current_state)
        
        # Print register usage for this cycle
        if self.debug:
            self.register_debugger.print_cycle_registers()
        
        return True
    
    def _get_instruction_at_pc(self, pc):
        """Get the instruction at the given PC."""
        try:
            return self.memory.read_word(pc)
        except:
            return None

    def _decode_stage(self):
        """Decode stage with fixed operand handling."""
        if self.flush:
            print("Flush active in decode stage, clearing IF/ID pipeline register")
            self.if_id.clear()
            self.flush = False
            return
        
        instruction = self.if_id.read("instruction")
        if instruction is None:
            return
        
        decoded = self.control_unit.decode(instruction)
        
        # Debug the decoded instruction
        print(f"Decoded instruction: opcode={decoded['opcode']}, dest_reg={decoded['dest_reg']}, " +
            f"src1_reg={decoded['src1_reg']}, src2_reg={decoded['src2_reg']}, imm={decoded['immediate']}")
        
        # Track register reads in decode stage
        src1_reg = decoded["src1_reg"]
        src1_val = self.reg_file.read(src1_reg)
        self.register_debugger.track_register_read('decode', src1_reg, src1_val)
        
        src2_val = 0  # Default for instructions not needing src2
        if not (decoded["opcode"] in [self.control_unit.BEQ, self.control_unit.BNE,
                                    self.control_unit.BLT, self.control_unit.BGE]):
            src2_reg = decoded["src2_reg"]
            src2_val = self.reg_file.read(src2_reg)
            self.register_debugger.track_register_read('decode', src2_reg, src2_val)
        
        # Write to ID/EX pipeline register
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
        self.id_ex.write("instruction", instruction)
        
        if self.debug:
            print(f"Decoded instruction 0x{instruction:08X} at PC=0x{self.if_id.read('pc'):08X}")
            print(f"  Control signals: {self.control_unit.__dict__}")
            print(f"  Src1 val: {src1_val}, Src2 val: {src2_val}, Immediate: {decoded['immediate']}")

    def _fetch_stage(self):
        """Instruction Fetch (IF) stage."""
        if self.flush:
            print("Flush active in fetch stage, clearing IF/ID pipeline register")
            self.if_id.clear()
            self.flush = False
            return
        
        if not self.stall:
            try:
                instruction = self.memory.read_word(self.reg_file.pc)
                self.if_id.write("instruction", instruction)
                self.if_id.write("pc", self.reg_file.pc)
                
                # Track PC register in fetch stage
                self.register_debugger.track_register_read('fetch', 'pc', self.reg_file.pc)
                
                if self.debug:
                    print(f"Fetched instruction 0x{instruction:08X} at PC=0x{self.reg_file.pc:08X}")
                self.reg_file.pc += 4
            except ValueError as e:
                print(f"Fetch error: {e}")
                self.control_unit.halt_flag = True
        else:
            if self.debug:
                print(f"Fetch stage stalled at PC=0x{self.reg_file.pc:08X}")


    def _execute_stage(self):
        """Execute (EX) stage with fixed operand handling."""
        control = self.id_ex.read("control")
        if control is None:
            return
        
        instruction = self.id_ex.read("instruction")
        src1_val = self.id_ex.read("src1_val")
        src2_val = self.id_ex.read("src2_val")
        immediate = self.id_ex.read("immediate")
        opcode = self.id_ex.read("opcode")
        src1_reg = self.id_ex.read("src1_reg")
        src2_reg = self.id_ex.read("src2_reg")
        pc = self.id_ex.read("pc")
        
        # Debug the register values
        print(f"Execute stage: src1_reg=R{src1_reg}({src1_val}), src2_reg=R{src2_reg}({src2_val})")
        
        # Track register usage in execute stage
        self.register_debugger.track_register_read('execute', src1_reg, src1_val)
        
        if not control["alu_src"]:  # Only if using register for src2
            self.register_debugger.track_register_read('execute', src2_reg, src2_val)
        
        # Track if forwarding has occurred
        forwarded_src1 = False
        forwarded_src2 = False
        
        # Forward from EX/MEM (highest priority)
        if self.ex_mem.read("control") and self.ex_mem.read("control").get("reg_write"):
            ex_mem_dest = self.ex_mem.read("dest_reg")
            if ex_mem_dest != 0:  # R0 is always 0
                # Forward to src1 if needed
                if ex_mem_dest == src1_reg and not forwarded_src1:
                    src1_val = self.ex_mem.read("alu_result")
                    forwarded_src1 = True
                    print(f"Forwarding EX/MEM to src1: R{src1_reg} = {src1_val}")
                
                # Forward to src2 if needed and not using immediate
                if not control["alu_src"] and ex_mem_dest == src2_reg and not forwarded_src2:
                    src2_val = self.ex_mem.read("alu_result")
                    forwarded_src2 = True
                    print(f"Forwarding EX/MEM to src2: R{src2_reg} = {src2_val}")
        
        # Forward from MEM/WB (lower priority)
        if self.mem_wb.read("control") and self.mem_wb.read("control").get("reg_write"):
            mem_wb_dest = self.mem_wb.read("dest_reg")
            if mem_wb_dest != 0:  # R0 is always 0
                # Get the correct data
                mem_wb_data = self.mem_wb.read("alu_result")
                if self.mem_wb.read("control").get("mem_to_reg") and self.mem_wb.read("mem_data") is not None:
                    mem_wb_data = self.mem_wb.read("mem_data")
                
                # Forward to src1 if needed and not already forwarded
                if mem_wb_dest == src1_reg and not forwarded_src1:
                    src1_val = mem_wb_data
                    forwarded_src1 = True
                    print(f"Forwarding MEM/WB to src1: R{src1_reg} = {src1_val}")
                
                # Forward to src2 if needed and not already forwarded
                if not control["alu_src"] and mem_wb_dest == src2_reg and not forwarded_src2:
                    src2_val = mem_wb_data
                    forwarded_src2 = True
                    print(f"Forwarding MEM/WB to src2: R{src2_reg} = {src2_val}")
        
        # After all forwarding, print the final values
        print(f"Final operand values: src1=R{src1_reg}({src1_val}), src2=" + 
            (f"R{src2_reg}({src2_val})" if not control["alu_src"] else f"imm({immediate})"))
        
        # Use the potentially forwarded values
        operand2 = immediate if control["alu_src"] else src2_val
        
        # Execute ALU operation
        if opcode == self.control_unit.MOVI:
            alu_op = self.alu.OP_MOV
        else:
            alu_op = opcode & 0x0F
        
        # Print the operation for debugging
        if alu_op == self.alu.OP_XOR:
            print(f"XOR: {src1_val} ^ {operand2} == {src1_val ^ operand2}")
        elif alu_op == self.alu.OP_ADD:
            print(f"ADD: {src1_val} + {operand2}")
        elif alu_op == self.alu.OP_SUB:
            print(f"SUB: {src1_val} - {operand2}")
        
        result = self.alu.execute(alu_op, src1_val, operand2)
        
        branch_target = None
        if control["branch"] or control["jump"]:
            branch_target = pc + (immediate << 2)
        
        self.ex_mem.write("control", control)
        self.ex_mem.write("alu_result", result)
        self.ex_mem.write("src2_val", src2_val)
        self.ex_mem.write("dest_reg", self.id_ex.read("dest_reg"))
        self.ex_mem.write("branch_target", branch_target)
        self.ex_mem.write("opcode", opcode)
        
        # Pass the instruction to the next stage
        self.ex_mem.write("instruction", instruction)
        
        take_branch = False
        if control["branch"]:
            if opcode == self.control_unit.BEQ:
                take_branch = (src1_val == src2_val)
            elif opcode == self.control_unit.BNE:
                take_branch = (src1_val != src2_val)
            elif opcode == self.control_unit.BLT:
                take_branch = (src1_val < src2_val)
            elif opcode == self.control_unit.BGE:
                take_branch = (src1_val >= src2_val)
            
            if self.debug:
                print(f"Branch instruction at PC=0x{pc:08X}")
                print(f"  Registers: src1_val={src1_val}, src2_val={src2_val}")
                print(f"  Immediate: {immediate} -> branch_target=0x{branch_target:08X}")
                print(f"  Branch taken? {take_branch}")
            
            if take_branch and branch_target is not None:
                if self.debug:
                    print(f"Branch taken: Jumping to 0x{branch_target:08X}")
                self.reg_file.pc = branch_target
                self.flush = True
                # Track PC update in execute stage for branch
                self.register_debugger.track_register_write('execute', 'pc', branch_target)
        elif control["jump"]:
            if self.debug:
                print(f"Jump instruction at PC=0x{pc:08X} jumping to 0x{branch_target:08X}")
            self.reg_file.pc = branch_target
            self.flush = True
            # Track PC update in execute stage for jump
            self.register_debugger.track_register_write('execute', 'pc', branch_target)
        
        # In execute_stage, make sure to forward from ALL pipeline stages
        # Forward from EX/MEM
        if self.ex_mem.read("control") and self.ex_mem.read("control").get("reg_write"):
            ex_mem_dest = self.ex_mem.read("dest_reg")
            if ex_mem_dest == src1_reg:
                src1_val = self.ex_mem.read("alu_result")
                print(f"Forwarding EX/MEM to src1: R{src1_reg} = {src1_val}")

        # Forward from MEM/WB
        if self.mem_wb.read("control") and self.mem_wb.read("control").get("reg_write"):
            mem_wb_dest = self.mem_wb.read("dest_reg")
            if mem_wb_dest == src1_reg:
                mem_wb_data = self.mem_wb.read("alu_result")
                if self.mem_wb.read("control").get("mem_to_reg"):
                    mem_wb_data = self.mem_wb.read("mem_data")
                src1_val = mem_wb_data
                print(f"Forwarding MEM/WB to src1: R{src1_reg} = {src1_val}")

    
    def _memory_stage(self):
        """Memory Access (MEM) stage."""
        control = self.ex_mem.read("control")
        if control is None:
            return  # Nothing to access
        
        alu_result = self.ex_mem.read("alu_result")
        instruction = self.ex_mem.read("instruction")
        mem_data = None
        
        try:
            if control["mem_read"]:
                # Load operation
                mem_data = self.memory.read_word(alu_result)
                # Track memory read
                self.register_debugger.track_register_read('memory', 'mem', alu_result)
            elif control["mem_write"]:
                # Store operation
                src2_val = self.ex_mem.read("src2_val")
                self.memory.write_word(alu_result, src2_val)
                # Track memory write
                self.register_debugger.track_register_write('memory', 'mem', src2_val)
        except ValueError as e:
            if self.debug:
                print(f"Memory access error: {e}")
            self.control_unit.halt_flag = True
        
        # Pass values to MEM/WB register
        self.mem_wb.write("control", control)
        self.mem_wb.write("alu_result", alu_result)
        self.mem_wb.write("mem_data", mem_data)
        self.mem_wb.write("dest_reg", self.ex_mem.read("dest_reg"))
        
        # Pass the instruction to the next stage
        self.mem_wb.write("instruction", instruction)
    
    def _writeback_stage(self):
        """Write Back (WB) stage with tracking to prevent multiple writebacks."""
        control = self.mem_wb.read("control")
        instruction = self.mem_wb.read("instruction")
        
        # Skip if nothing to write back or instruction already completed
        if control is None or getattr(self, "_completed_instructions", set()).intersection({instruction}):
            return
        
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
                # Track register write in writeback stage
                self.register_debugger.track_register_write('writeback', dest_reg, write_data)
                print(f"Writeback: Writing {write_data} to R{dest_reg}")
            
            self.instructions_executed += 1
        
        # Mark this instruction as completed
        if not hasattr(self, "_completed_instructions"):
            self._completed_instructions = set()
        if instruction is not None:
            self._completed_instructions.add(instruction)
    
    def _hazard_detection(self):
        """Optimized hazard detection to minimize unnecessary stalls."""
        # Reset stall flag by default
        should_stall = False
        stall_reason = ""
        
        # Get the instruction in decode stage
        if_id_instr = self.if_id.read("instruction")
        if if_id_instr is None:
            self.stall = False
            return
        
        # Decode the instruction to check register dependencies
        decoded = self.control_unit.decode(if_id_instr)
        src1_reg = decoded["src1_reg"]
        src2_reg = decoded["src2_reg"]
        uses_src2 = not decoded.get("alu_src", False)  # Only check src2 if not using immediate
        
        # Check if ID/EX is writing to a register that IF/ID needs to read
        if self.id_ex.read("control") and self.id_ex.read("control").get("reg_write"):
            id_ex_dest = self.id_ex.read("dest_reg")
            
            # Only stall if:
            # 1. The destination register is not R0
            # 2. The destination register is needed by the next instruction
            # 3. The instruction in ID/EX is a load (which won't have result until MEM stage)
            if (id_ex_dest != 0 and 
                (id_ex_dest == src1_reg or (uses_src2 and id_ex_dest == src2_reg)) and
                self.id_ex.read("control").get("mem_read")):
                
                should_stall = True
                stall_reason = f"ID/EX load writing to R{id_ex_dest}, needed by next instruction"
        
        # Check if EX/MEM is writing to a register that IF/ID needs to read
        # Only stall if we can't forward the result (e.g., for loads)
        if not should_stall and self.ex_mem.read("control") and self.ex_mem.read("control").get("reg_write"):
            ex_mem_dest = self.ex_mem.read("dest_reg")
            
            # Only stall for loads, as other results can be forwarded
            if (ex_mem_dest != 0 and 
                (ex_mem_dest == src1_reg or (uses_src2 and ex_mem_dest == src2_reg)) and
                self.ex_mem.read("control").get("mem_read")):
                
                should_stall = True
                stall_reason = f"EX/MEM load writing to R{ex_mem_dest}, needed by next instruction"
        
        # Update stall status
        if should_stall:
            self.stall = True
            self.stall_cycles += 1
            print(f"Stalling: {stall_reason}")
        else:
            self.stall = False