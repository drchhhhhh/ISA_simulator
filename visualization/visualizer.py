import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation
import matplotlib.patches as patches
from collections import defaultdict
import copy

class SimulationVisualizer:
    """Visualizes the execution of the ISA simulator."""
    
    def __init__(self, simulator):
        """Initialize the visualizer."""
        self.simulator = simulator
        self.history = {
            'pc': [],
            'registers': [],
            'memory_accesses': [],
            'pipeline_states': [],
            'instructions': [],
            'cycles': []
        }
        self.memory_access_log = []
        self.instruction_count = defaultdict(int)
        
        # Color scheme for visualization
        self.colors = {
            'fetch': '#FFD700',      # Gold
            'decode': '#87CEEB',     # Sky Blue
            'execute': '#90EE90',    # Light Green
            'memory': '#FFA07A',     # Light Salmon
            'writeback': '#DDA0DD',  # Plum
            'stall': '#D3D3D3',      # Light Gray
            'flush': '#FF6347'       # Tomato
        }
    
    def record_state(self):
        """Record the current state of the simulator."""
        # Record PC
        self.history['pc'].append(self.simulator.reg_file.pc)
        
        # Record registers (deep copy to avoid reference issues)
        self.history['registers'].append(copy.deepcopy(self.simulator.reg_file.registers))
        
        # Record cycle number
        self.history['cycles'].append(self.simulator.cycles)
        
        # Record pipeline state
        pipeline_state = {
            'if_id': self._get_pipeline_state(self.simulator.if_id),
            'id_ex': self._get_pipeline_state(self.simulator.id_ex),
            'ex_mem': self._get_pipeline_state(self.simulator.ex_mem),
            'mem_wb': self._get_pipeline_state(self.simulator.mem_wb),
            'stall': self.simulator.stall,
            'flush': self.simulator.flush
        }
        self.history['pipeline_states'].append(pipeline_state)
        
        # Record memory accesses
        if self.simulator.ex_mem.read('control') is not None:
            control = self.simulator.ex_mem.read('control')
            if control.get('mem_read') or control.get('mem_write'):
                address = self.simulator.ex_mem.read('alu_result')
                access_type = 'read' if control.get('mem_read') else 'write'
                value = self.simulator.mem_wb.read('mem_data') if access_type == 'read' else self.simulator.ex_mem.read('src2_val')
                
                self.memory_access_log.append({
                    'cycle': self.simulator.cycles,
                    'address': address,
                    'type': access_type,
                    'value': value
                })
        
        # Record instruction information
        if self.simulator.if_id.read('instruction') is not None:
            instruction = self.simulator.if_id.read('instruction')
            opcode = (instruction >> 24) & 0xFF
            self.instruction_count[opcode] += 1
            
            self.history['instructions'].append({
                'pc': self.simulator.if_id.read('pc'),
                'instruction': instruction,
                'opcode': opcode
            })
    
    def _get_pipeline_state(self, pipeline_reg):
        """Extract relevant information from a pipeline register."""
        if not pipeline_reg.data:
            return None
        
        # Extract key information based on pipeline stage
        if pipeline_reg.name == "IF/ID":
            return {
                'instruction': pipeline_reg.read('instruction'),
                'pc': pipeline_reg.read('pc')
            }
        elif pipeline_reg.name == "ID/EX":
            return {
                'opcode': pipeline_reg.read('opcode'),
                'src1_val': pipeline_reg.read('src1_val'),
                'src2_val': pipeline_reg.read('src2_val'),
                'immediate': pipeline_reg.read('immediate'),
                'dest_reg': pipeline_reg.read('dest_reg'),
                'control': pipeline_reg.read('control')
            }
        elif pipeline_reg.name == "EX/MEM":
            return {
                'alu_result': pipeline_reg.read('alu_result'),
                'dest_reg': pipeline_reg.read('dest_reg'),
                'control': pipeline_reg.read('control')
            }
        elif pipeline_reg.name == "MEM/WB":
            return {
                'alu_result': pipeline_reg.read('alu_result'),
                'mem_data': pipeline_reg.read('mem_data'),
                'dest_reg': pipeline_reg.read('dest_reg'),
                'control': pipeline_reg.read('control')
            }
        return None
    
    def plot_register_history(self, registers_to_plot=None):
        """Plot the history of register values."""
        if not self.history['registers']:
            print("No register history to plot.")
            return
        
        # Default to plotting first 8 registers if none specified
        if registers_to_plot is None:
            registers_to_plot = list(range(8))
        
        cycles = self.history['cycles']
        
        plt.figure(figsize=(12, 8))
        for reg in registers_to_plot:
            values = [regs[reg] for regs in self.history['registers']]
            plt.plot(cycles, values, marker='o', label=f'R{reg}')
        
        plt.title('Register Values Over Time')
        plt.xlabel('Cycle')
        plt.ylabel('Value')
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.show()
    
    def plot_pipeline_activity(self):
        """Plot the pipeline activity over time."""
        if not self.history['pipeline_states']:
            print("No pipeline history to plot.")
            return
        
        cycles = self.history['cycles']
        num_cycles = len(cycles)
        
        # Create figure
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Pipeline stages
        stages = ['Fetch', 'Decode', 'Execute', 'Memory', 'Writeback']
        
        # Plot grid
        for i in range(num_cycles + 1):
            ax.axvline(x=i, color='gray', linestyle='-', alpha=0.3)
        
        for i in range(len(stages) + 1):
            ax.axhline(y=i, color='gray', linestyle='-', alpha=0.3)
        
        # Plot pipeline activity
        for cycle_idx, cycle in enumerate(cycles):
            pipeline_state = self.history['pipeline_states'][cycle_idx]
            
            # Check for stalls and flushes
            stall = pipeline_state.get('stall', False)
            flush = pipeline_state.get('flush', False)
            
            # Plot each stage
            stages_data = [
                pipeline_state.get('if_id'),
                pipeline_state.get('id_ex'),
                pipeline_state.get('ex_mem'),
                pipeline_state.get('mem_wb')
            ]
            
            for stage_idx, stage_data in enumerate(stages_data):
                if stage_data is not None:
                    # Determine color based on stage and stall/flush status
                    if stall and stage_idx == 0:  # Stall affects fetch
                        color = self.colors['stall']
                    elif flush and stage_idx == 0:  # Flush affects fetch
                        color = self.colors['flush']
                    else:
                        color = list(self.colors.values())[stage_idx]
                    
                    # Add rectangle for this stage
                    rect = patches.Rectangle(
                        (cycle_idx, stage_idx), 1, 1, 
                        linewidth=1, edgecolor='black', facecolor=color, alpha=0.7
                    )
                    ax.add_patch(rect)
                    
                    # Add instruction info if available
                    if stage_idx == 0 and 'instruction' in stage_data:
                        instr = stage_data['instruction']
                        opcode = (instr >> 24) & 0xFF if instr is not None else None
                        if opcode is not None:
                            ax.text(cycle_idx + 0.5, stage_idx + 0.5, f"Op: {opcode:02X}", 
                                   ha='center', va='center', fontsize=8)
        
        # Set labels and title
        ax.set_xticks(range(num_cycles + 1))
        ax.set_xticklabels(range(num_cycles + 1))
        ax.set_yticks(range(len(stages) + 1))
        ax.set_yticklabels([''] + stages)
        ax.set_xlabel('Cycle')
        ax.set_title('Pipeline Activity')
        
        # Add legend
        legend_elements = [
            patches.Patch(facecolor=self.colors['fetch'], edgecolor='black', label='Fetch'),
            patches.Patch(facecolor=self.colors['decode'], edgecolor='black', label='Decode'),
            patches.Patch(facecolor=self.colors['execute'], edgecolor='black', label='Execute'),
            patches.Patch(facecolor=self.colors['memory'], edgecolor='black', label='Memory'),
            patches.Patch(facecolor=self.colors['writeback'], edgecolor='black', label='Writeback'),
            patches.Patch(facecolor=self.colors['stall'], edgecolor='black',  label='Writeback'),
            patches.Patch(facecolor=self.colors['stall'], edgecolor='black', label='Stall'),
            patches.Patch(facecolor=self.colors['flush'], edgecolor='black', label='Flush')
        ]
        ax.legend(handles=legend_elements, loc='upper center', bbox_to_anchor=(0.5, -0.05),
                 fancybox=True, shadow=True, ncol=7)
        
        plt.tight_layout()
        plt.show()
    
    def animate_pipeline(self, interval=500, frames=None):
        """Create an animation of the pipeline execution."""
        if not self.history['pipeline_states']:
            print("No pipeline history to animate.")
            return
        
        cycles = self.history['cycles']
        num_cycles = len(cycles)
        
        if frames is None:
            frames = num_cycles
        else:
            frames = min(frames, num_cycles)
        
        # Create figure
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Pipeline stages
        stages = ['Fetch', 'Decode', 'Execute', 'Memory', 'Writeback']
        
        def init():
            ax.clear()
            # Set up the grid
            for i in range(frames + 1):
                ax.axvline(x=i, color='gray', linestyle='-', alpha=0.3)
            
            for i in range(len(stages) + 1):
                ax.axhline(y=i, color='gray', linestyle='-', alpha=0.3)
            
            # Set labels and title
            ax.set_xticks(range(frames + 1))
            ax.set_xticklabels(range(frames + 1))
            ax.set_yticks(range(len(stages) + 1))
            ax.set_yticklabels([''] + stages)
            ax.set_xlabel('Cycle')
            ax.set_title('Pipeline Animation')
            
            return []
        
        def update(frame):
            ax.clear()
            
            # Set up the grid
            for i in range(frames + 1):
                ax.axvline(x=i, color='gray', linestyle='-', alpha=0.3)
            
            for i in range(len(stages) + 1):
                ax.axhline(y=i, color='gray', linestyle='-', alpha=0.3)
            
            # Plot pipeline activity up to current frame
            for cycle_idx in range(min(frame + 1, num_cycles)):
                pipeline_state = self.history['pipeline_states'][cycle_idx]
                
                # Check for stalls and flushes
                stall = pipeline_state.get('stall', False)
                flush = pipeline_state.get('flush', False)
                
                # Plot each stage
                stages_data = [
                    pipeline_state.get('if_id'),
                    pipeline_state.get('id_ex'),
                    pipeline_state.get('ex_mem'),
                    pipeline_state.get('mem_wb')
                ]
                
                for stage_idx, stage_data in enumerate(stages_data):
                    if stage_data is not None:
                        # Determine color based on stage and stall/flush status
                        if stall and stage_idx == 0:  # Stall affects fetch
                            color = self.colors['stall']
                        elif flush and stage_idx == 0:  # Flush affects fetch
                            color = self.colors['flush']
                        else:
                            color = list(self.colors.values())[stage_idx]
                        
                        # Add rectangle for this stage
                        rect = patches.Rectangle(
                            (cycle_idx, stage_idx), 1, 1, 
                            linewidth=1, edgecolor='black', facecolor=color, alpha=0.7
                        )
                        ax.add_patch(rect)
                        
                        # Add instruction info if available
                        if stage_idx == 0 and 'instruction' in stage_data:
                            instr = stage_data['instruction']
                            opcode = (instr >> 24) & 0xFF if instr is not None else None
                            if opcode is not None:
                                ax.text(cycle_idx + 0.5, stage_idx + 0.5, f"Op: {opcode:02X}", 
                                       ha='center', va='center', fontsize=8)
            
            # Set labels and title
            ax.set_xticks(range(frames + 1))
            ax.set_xticklabels(range(frames + 1))
            ax.set_yticks(range(len(stages) + 1))
            ax.set_yticklabels([''] + stages)
            ax.set_xlabel('Cycle')
            ax.set_title(f'Pipeline Animation - Cycle {frame}')
            
            # Add legend
            legend_elements = [
                patches.Patch(facecolor=self.colors['fetch'], edgecolor='black', label='Fetch'),
                patches.Patch(facecolor=self.colors['decode'], edgecolor='black', label='Decode'),
                patches.Patch(facecolor=self.colors['execute'], edgecolor='black', label='Execute'),
                patches.Patch(facecolor=self.colors['memory'], edgecolor='black', label='Memory'),
                patches.Patch(facecolor=self.colors['writeback'], edgecolor='black', label='Writeback'),
                patches.Patch(facecolor=self.colors['stall'], edgecolor='black', label='Stall'),
                patches.Patch(facecolor=self.colors['flush'], edgecolor='black', label='Flush')
            ]
            ax.legend(handles=legend_elements, loc='upper center', bbox_to_anchor=(0.5, -0.05),
                     fancybox=True, shadow=True, ncol=7)
            
            return []
        
        ani = FuncAnimation(fig, update, frames=frames, init_func=init, blit=True, interval=interval)
        plt.tight_layout()
        plt.show()
        
        return ani
    
    def plot_instruction_mix(self):
        """Plot the mix of instructions executed."""
        if not self.instruction_count:
            print("No instructions executed.")
            return
        
        # Map opcodes to instruction types
        opcode_types = {
            # Data processing
            0x00: "ADD", 0x01: "SUB", 0x02: "AND", 0x03: "OR", 0x04: "XOR",
            0x05: "SLL", 0x06: "SRL", 0x07: "SRA", 0x08: "SLT", 0x09: "MUL", 0x0A: "DIV",
            0x10: "ADDI", 0x11: "SUBI", 0x12: "ANDI", 0x13: "ORI", 0x14: "XORI",
            0x15: "SLLI", 0x16: "SRLI", 0x17: "SRAI", 0x18: "SLTI", 0x1F: "MOV",
            
            # Memory access
            0x20: "LOAD", 0x21: "STORE", 0x22: "PUSH", 0x23: "POP",
            
            # Control flow
            0x40: "JMP", 0x41: "BEQ", 0x42: "BNE", 0x43: "BLT", 0x44: "BGE", 0x45: "CALL", 0x46: "RET",
            
            # System operations
            0x60: "HALT", 0x61: "IO_READ", 0x62: "IO_WRITE"
        }
        
        # Group by instruction type
        instruction_types = defaultdict(int)
        for opcode, count in self.instruction_count.items():
            instr_name = opcode_types.get(opcode, f"Unknown ({opcode:02X})")
            instruction_types[instr_name] += count
        
        # Create pie chart
        plt.figure(figsize=(10, 8))
        labels = list(instruction_types.keys())
        sizes = list(instruction_types.values())
        
        # Use a colorful palette
        plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, shadow=True)
        plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
        plt.title('Instruction Mix')
        plt.tight_layout()
        plt.show()
    
    def plot_memory_access_pattern(self):
        """Plot memory access patterns."""
        if not self.memory_access_log:
            print("No memory accesses recorded.")
            return
        
        # Extract data
        cycles = [access['cycle'] for access in self.memory_access_log]
        addresses = [access['address'] for access in self.memory_access_log]
        access_types = [access['type'] for access in self.memory_access_log]
        
        # Create scatter plot
        plt.figure(figsize=(12, 8))
        
        # Plot reads and writes with different colors
        read_indices = [i for i, t in enumerate(access_types) if t == 'read']
        write_indices = [i for i, t in enumerate(access_types) if t == 'write']
        
        if read_indices:
            plt.scatter([cycles[i] for i in read_indices], [addresses[i] for i in read_indices], 
                       color='blue', marker='o', label='Read')
        
        if write_indices:
            plt.scatter([cycles[i] for i in write_indices], [addresses[i] for i in write_indices], 
                       color='red', marker='x', label='Write')
        
        plt.title('Memory Access Pattern')
        plt.xlabel('Cycle')
        plt.ylabel('Memory Address')
        plt.yscale('log')  # Log scale for better visualization of address ranges
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.show()
    
    def print_execution_trace(self):
        """Print a textual trace of the execution."""
        if not self.history['cycles']:
            print("No execution history to trace.")
            return
        
        print("=== Execution Trace ===")
        print(f"{'Cycle':^6} | {'PC':^10} | {'Instruction':^12} | {'Registers':^30} | {'Flags':^20}")
        print("-" * 85)
        
        for i, cycle in enumerate(self.history['cycles']):
            pc = self.history['pc'][i]
            
            # Get instruction info if available
            instr_info = ""
            if i < len(self.history['instructions']) and self.history['instructions'][i]:
                instr = self.history['instructions'][i]
                opcode = instr.get('opcode')
                if opcode is not None:
                    instr_info = f"Op: {opcode:02X}"
            
            # Get register changes
            reg_changes = []
            if i > 0:  # Compare with previous cycle
                for reg_num in range(len(self.history['registers'][i])):
                    if self.history['registers'][i][reg_num] != self.history['registers'][i-1][reg_num]:
                        reg_changes.append(f"R{reg_num}={self.history['registers'][i][reg_num]}")
            
            # Get flags if available
            flags_info = ""
            if hasattr(self.simulator.reg_file, 'zero_flag'):
                flags_info = f"Z={int(self.simulator.reg_file.zero_flag)} "
            if hasattr(self.simulator.reg_file, 'negative_flag'):
                flags_info += f"N={int(self.simulator.reg_file.negative_flag)} "
            if hasattr(self.simulator.reg_file, 'carry_flag'):
                flags_info += f"C={int(self.simulator.reg_file.carry_flag)} "
            if hasattr(self.simulator.reg_file, 'overflow_flag'):
                flags_info += f"V={int(self.simulator.reg_file.overflow_flag)}"
            
            print(f"{cycle:^6} | {pc:^10X} | {instr_info:^12} | {', '.join(reg_changes):^30} | {flags_info:^20}")
        
        print("\n=== Performance Summary ===")
        print(f"Total Cycles: {self.simulator.cycles}")
        print(f"Instructions Executed: {self.simulator.instructions_executed}")
        print(f"Stall Cycles: {self.simulator.stall_cycles}")
        
        if self.simulator.cycles > 0:
            ipc = self.simulator.instructions_executed / self.simulator.cycles
            print(f"Instructions Per Cycle (IPC): {ipc:.2f}")
        
        print("\n=== Instruction Mix ===")
        for opcode, count in sorted(self.instruction_count.items()):
            print(f"Opcode 0x{opcode:02X}: {count} instructions")