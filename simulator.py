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
        
        current_state = {
            'fetch': self._get_instruction_at_pc(self.reg_file.pc),
            'decode': self.if_id.read("instruction"),
            'execute': self.id_ex.read("instruction"),
            'memory': self.ex_mem.read("instruction"),
            'writeback': self.mem_wb.read("instruction")
        }
        
        # Execute pipeline stages in reverse order to avoid overwriting data
        self._writeback_stage()
        self._memory_stage()
        self._execute_stage()
        self._decode_stage()
        self._fetch_stage()
        
        # Detect hazards after executing all stages
        self._hazard_detection()
        
        self.cycles += 1
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
        """Instruction Decode (ID) stage with data forwarding."""
        if self.flush:
            if self.debug:
                print("Flush active in decode stage, clearing IF/ID pipeline register")
            self.if_id.clear()
            return
        
        instruction = self.if_id.read("instruction")
        if instruction is None:
            return
        
        decoded = self.control_unit.decode(instruction)
        
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
        
        # ===== DATA FORWARDING TO DECODE STAGE =====
        # Forward from EX/MEM if needed
        if (self.ex_mem.read("control") and 
            self.ex_mem.read("control").get("reg_write") and 
            self.ex_mem.read("dest_reg") != 0):
            
            ex_mem_dest = self.ex_mem.read("dest_reg")
            
            # Forward to src1 if needed
            if ex_mem_dest == src1_reg:
                src1_val = self.ex_mem.read("alu_result")
                if self.debug:
                    print(f"Forwarding EX/MEM to src1 in decode: R{src1_reg} = {src1_val}")
            
            # Forward to src2 if needed
            if ex_mem_dest == src2_reg:
                src2_val = self.ex_mem.read("alu_result")
                if self.debug:
                    print(f"Forwarding EX/MEM to src2 in decode: R{src2_reg} = {src2_val}")

        # Forward from MEM/WB if needed
        if (self.mem_wb.read("control") and 
            self.mem_wb.read("control").get("reg_write") and 
            self.mem_wb.read("dest_reg") != 0):
            
            mem_wb_dest = self.mem_wb.read("dest_reg")
            mem_wb_data = self.mem_wb.read("alu_result")
            
            # If loading from memory, use memory data
            if self.mem_wb.read("control").get("mem_to_reg") and self.mem_wb.read("mem_data") is not None:
                mem_wb_data = self.mem_wb.read("mem_data")
            
            # Forward to src1 if needed (and not already forwarded from EX/MEM)
            if mem_wb_dest == src1_reg:
                # Only forward if EX/MEM isn't already forwarding to this register
                if not (self.ex_mem.read("control") and 
                    self.ex_mem.read("control").get("reg_write") and 
                    self.ex_mem.read("dest_reg") == src1_reg):
                    src1_val = mem_wb_data
                    if self.debug:
                        print(f"Forwarding MEM/WB to src1 in decode: R{src1_reg} = {src1_val}")
            
            # Forward to src2 if needed (and not already forwarded from EX/MEM)
            if mem_wb_dest == src2_reg:
                # Only forward if EX/MEM isn't already forwarding to this register
                if not (self.ex_mem.read("control") and 
                    self.ex_mem.read("control").get("reg_write") and 
                    self.ex_mem.read("dest_reg") == src2_reg):
                    src2_val = mem_wb_data
                    if self.debug:
                        print(f"Forwarding MEM/WB to src2 in decode: R{src2_reg} = {src2_val}")
        # ===== END DATA FORWARDING TO DECODE STAGE =====
        
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
        
        # Pass the instruction to the next stage
        self.id_ex.write("instruction", instruction)
        
        if self.debug:
            print(f"Decoded instruction 0x{instruction:08X} at PC=0x{self.if_id.read('pc'):08X}")
            print(f"  Control signals: {self.control_unit.__dict__}")
            print(f"  Src1 val: {src1_val}, Src2 val: {src2_val}, Immediate: {decoded['immediate']}")

    def _fetch_stage(self):
        """Instruction Fetch (IF) stage."""
        if self.flush:
            if self.debug:
                print("Flush active in fetch stage, clearing IF/ID pipeline register")
            self.if_id.clear()
            self.flush = False  # Reset flush after handling
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
        """Execute (EX) stage with data forwarding."""
        control = self.id_ex.read("control")
        if control is None:
            return
        
        src1_val = self.id_ex.read("src1_val")
        src2_val = self.id_ex.read("src2_val")
        immediate = self.id_ex.read("immediate")
        opcode = self.id_ex.read("opcode")
        pc = self.id_ex.read("pc")
        instruction = self.id_ex.read("instruction")
        
        # Get register numbers for forwarding
        src1_reg = self.id_ex.read("src1_reg")
        src2_reg = self.id_ex.read("src2_reg")
        
        # Track register usage in execute stage
        self.register_debugger.track_register_read('execute', src1_reg, src1_val)
        
        if not control["alu_src"]:  # Only if using register for src2
            self.register_debugger.track_register_read('execute', src2_reg, src2_val)
        
        # ===== DATA FORWARDING LOGIC =====
        
        # Forward from EX/MEM if needed
        if (self.ex_mem.read("control") and 
            self.ex_mem.read("control").get("reg_write") and 
            self.ex_mem.read("dest_reg") != 0):
            
            ex_mem_dest = self.ex_mem.read("dest_reg")
            
            # Forward to src1 if needed
            if ex_mem_dest == src1_reg:
                src1_val = self.ex_mem.read("alu_result")
                if self.debug:
                    print(f"Forwarding EX/MEM to src1: R{src1_reg} = {src1_val}")
            
            # Forward to src2 if needed (and not using immediate)
            if not control["alu_src"] and ex_mem_dest == src2_reg:
                src2_val = self.ex_mem.read("alu_result")
                if self.debug:
                    print(f"Forwarding EX/MEM to src2: R{src2_reg} = {src2_val}")
        
        # Forward from MEM/WB if needed
        if (self.mem_wb.read("control") and 
            self.mem_wb.read("control").get("reg_write") and 
            self.mem_wb.read("dest_reg") != 0):
            
            mem_wb_dest = self.mem_wb.read("dest_reg")
            mem_wb_data = self.mem_wb.read("alu_result")
            
            # If loading from memory, use memory data
            if self.mem_wb.read("control").get("mem_to_reg") and self.mem_wb.read("mem_data") is not None:
                mem_wb_data = self.mem_wb.read("mem_data")
            
            # Forward to src1 if needed (and not already forwarded from EX/MEM)
            if mem_wb_dest == src1_reg:
                # Only forward if EX/MEM isn't already forwarding to this register
                if not (self.ex_mem.read("control") and 
                       self.ex_mem.read("control").get("reg_write") and 
                       self.ex_mem.read("dest_reg") == src1_reg):
                    src1_val = mem_wb_data
                    if self.debug:
                        print(f"Forwarding MEM/WB to src1: R{src1_reg} = {src1_val}")
            
            # Forward to src2 if needed (and not using immediate, and not already forwarded from EX/MEM)
            if not control["alu_src"] and mem_wb_dest == src2_reg:
                # Only forward if EX/MEM isn't already forwarding to this register
                if not (self.ex_mem.read("control") and 
                       self.ex_mem.read("control").get("reg_write") and 
                       self.ex_mem.read("dest_reg") == src2_reg):
                    src2_val = mem_wb_data
                    if self.debug:
                        print(f"Forwarding MEM/WB to src2: R{src2_reg} = {src2_val}")
        
        # Special handling for MUL-DIV dependency
        if (opcode == self.control_unit.DIV and 
            self.ex_mem.read("opcode") == self.control_unit.MUL and
            self.ex_mem.read("dest_reg") == src1_reg):
            
            src1_val = self.ex_mem.read("alu_result")
            if self.debug:
                print(f"Special MUL-DIV forwarding: R{src1_reg} = {src1_val}")
        
        # ===== END DATA FORWARDING LOGIC =====
        
        # Use the potentially forwarded values
        operand2 = immediate if control["alu_src"] else src2_val
        
        # Determine ALU operation
        if opcode == self.control_unit.MOVI:
            alu_op = self.alu.OP_MOV
        else:
            alu_op = opcode & 0x0F
        
        # Execute ALU operation
        result = self.alu.execute(alu_op, src1_val, operand2)
        
        # Debug print for ALU operation
        if self.debug:
            op_names = {
                self.alu.OP_ADD: "ADD",
                self.alu.OP_SUB: "SUB",
                self.alu.OP_AND: "AND",
                self.alu.OP_OR: "OR",
                self.alu.OP_XOR: "XOR",
                self.alu.OP_SLL: "SLL",
                self.alu.OP_SRL: "SRL",
                self.alu.OP_SRA: "SRA",
                self.alu.OP_SLT: "SLT",
                self.alu.OP_MUL: "MUL",
                self.alu.OP_DIV: "DIV",
                self.alu.OP_MOV: "MOV"
            }
            op_name = op_names.get(alu_op, f"Unknown({alu_op})")
            print(f"{op_name}: {src1_val} {op_name.lower()} {operand2}")
        
        # Calculate branch target if needed
        branch_target = None
        if control["branch"] or control["jump"]:
            branch_target = pc + (immediate << 2)
        
        # Pass results to EX/MEM register
        self.ex_mem.write("control", control)
        self.ex_mem.write("alu_result", result)
        self.ex_mem.write("src2_val", src2_val)
        self.ex_mem.write("dest_reg", self.id_ex.read("dest_reg"))
        self.ex_mem.write("branch_target", branch_target)
        self.ex_mem.write("opcode", opcode)
        
        # Pass the instruction to the next stage
        self.ex_mem.write("instruction", instruction)
        
        # Handle branches and jumps
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
                if self.debug:
                    print(f"Memory read: address=0x{alu_result:08X}, data=0x{mem_data:08X}")
            elif control["mem_write"]:
                # Store operation
                src2_val = self.ex_mem.read("src2_val")
                self.memory.write_word(alu_result, src2_val)
                # Track memory write
                self.register_debugger.track_register_write('memory', 'mem', src2_val)
                if self.debug:
                    print(f"Memory write: address=0x{alu_result:08X}, data=0x{src2_val:08X}")
        except ValueError as e:
            if self.debug:
                print(f"Memory access error: {e}")
            self.control_unit.halt_flag = True
        
        # Pass values to MEM/WB register
        self.mem_wb.write("control", control)
        self.mem_wb.write("alu_result", alu_result)
        self.mem_wb.write("mem_data", mem_data)
        self.mem_wb.write("dest_reg", self.ex_mem.read("dest_reg"))
        self.mem_wb.write("opcode", self.ex_mem.read("opcode"))
        
        # Pass the instruction to the next stage
        self.mem_wb.write("instruction", instruction)
    
    def _writeback_stage(self):
        """Write Back (WB) stage."""
        control = self.mem_wb.read("control")
        if control is None:
            return  # Nothing to write back
        
        if control["reg_write"]:
            dest_reg = self.mem_wb.read("dest_reg")
            
            # Determine write data source
            if control["mem_to_reg"] and self.mem_wb.read("mem_data") is not None:
                write_data = self.mem_wb.read("mem_data")
            else:
                write_data = self.mem_wb.read("alu_result")
            
            # Write to register file (skip R0 which is hardwired to 0)
            if dest_reg != 0:
                self.reg_file.write(dest_reg, write_data)
                # Track register write in writeback stage
                self.register_debugger.track_register_write('writeback', dest_reg, write_data)
                if self.debug:
                    print(f"Writeback: R{dest_reg} = 0x{write_data:08X} ({write_data})")
            
            self.instructions_executed += 1
            
            # Check if this is a HALT instruction
            opcode = self.mem_wb.read("opcode")
            if opcode == self.control_unit.HALT:
                if self.debug:
                    print("HALT instruction in writeback stage")
                self.control_unit.halt_flag = True
    
    def _hazard_detection(self):
        """Enhanced hazard detection for data dependencies."""
        # Reset stall flag at the beginning of hazard detection
        stall_needed = False
        
        # Get the instruction in IF/ID stage
        if_id_instr = self.if_id.read("instruction")
        if if_id_instr is None:
            self.stall = stall_needed
            return
        
        # Decode the instruction to check register dependencies
        next_decoded = self.control_unit.decode(if_id_instr)
        next_src1 = next_decoded["src1_reg"]
        next_src2 = next_decoded["src2_reg"]
        
        # 1. Check ID/EX stage for RAW hazards
        if self.id_ex.read("control") and self.id_ex.read("control").get("reg_write"):
            id_ex_dest = self.id_ex.read("dest_reg")
            
            # Special handling for load instructions (need extra stall)
            if self.id_ex.read("control").get("mem_read") and id_ex_dest != 0:
                if id_ex_dest in [next_src1, next_src2]:
                    stall_needed = True
                    if self.debug:
                        print(f"Stalling: Load to R{id_ex_dest} in ID/EX, needed by next instruction")
        
        # 2. Check EX/MEM stage for RAW hazards
        if self.ex_mem.read("control") and self.ex_mem.read("control").get("reg_write"):
            ex_mem_dest = self.ex_mem.read("dest_reg")
            
            # Special handling for MUL-DIV dependency
            if (self.ex_mem.read("opcode") == self.control_unit.MUL and 
                next_decoded["opcode"] == self.control_unit.DIV and
                ex_mem_dest == next_src1):
                
                stall_needed = True
                if self.debug:
                    print(f"Stalling: MUL to R{ex_mem_dest} in EX/MEM, needed by DIV instruction")
        
        # 3. Check for structural hazards (not implemented in this simple model)
        
        # Update stall flag
        if stall_needed and not self.stall:
            self.stall_cycles += 1
        
        self.stall = stall_needed