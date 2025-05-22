import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
import time
import os

class ISASimulatorGUI:
    """Tkinter-based GUI for the ISA Simulator."""
    
    def __init__(self, root, simulator):
        self.root = root
        self.simulator = simulator
        self.root.title("ISA Simulator")
        self.root.geometry("1200x800")
        
        # Setup control variables
        self.running = False
        self.cycle_delay = tk.DoubleVar(value=0.5)  # seconds between cycles
        
        # Initialize set to track used registers
        self.used_registers = set()
        
        # Create main frame
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self.editor_tab = ttk.Frame(self.notebook)  # New editor tab
        self.simulator_tab = ttk.Frame(self.notebook)
        self.registers_tab = ttk.Frame(self.notebook)
        self.memory_tab = ttk.Frame(self.notebook)
        self.pipeline_tab = ttk.Frame(self.notebook)
        self.stats_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.editor_tab, text="Instruction Editor")  # Add editor tab first
        self.notebook.add(self.simulator_tab, text="Simulator")
        self.notebook.add(self.registers_tab, text="Registers")
        self.notebook.add(self.memory_tab, text="Memory")
        self.notebook.add(self.pipeline_tab, text="Pipeline")
        self.notebook.add(self.stats_tab, text="Statistics")
        
        # Setup each tab
        self._setup_editor_tab()  # Setup the new editor tab
        self._setup_simulator_tab()
        self._setup_registers_tab()
        self._setup_memory_tab()
        self._setup_pipeline_tab()
        self._setup_stats_tab()
        
        # Initialize state history
        self.state_history = []
        
        # Register update function
        self.root.after(100, self._update_display)
    
    def _setup_editor_tab(self):
        """Setup the instruction editor tab."""
        frame = ttk.Frame(self.editor_tab)
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create a frame for instruction input
        input_frame = ttk.LabelFrame(frame, text="Instruction Input")
        input_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create text editor for instruction input
        self.instruction_editor = scrolledtext.ScrolledText(input_frame, wrap=tk.WORD, height=15, font=("Courier", 10))
        self.instruction_editor.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Add example instructions as placeholder
        example_instructions = """ADD R1, R0, R2    ; R1 = R0 + R2
SUBI R3, R1, #5    ; R3 = R1 - 5
MOV R4, R3        ; R4 = R3

; Memory access
LOAD R5, [R4 + 8] ; Load from memory at address R4+8
STORE R5, [R0 + 16] ; Store R5 to memory at address R0+16

; Control flow
BEQ R1, R2, loop  ; Branch to 'loop' if R1 == R2
JMP end           ; Jump to 'end'

; Labels
loop:
    ADDI R6, R6, #1
    BNE R6, R7, loop
end:
    HALT          ; Stop execution
"""
        self.instruction_editor.insert(tk.END, example_instructions)
        
        # Control buttons
        btn_frame = ttk.Frame(input_frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(btn_frame, text="Assemble & Load", command=self._assemble_from_editor).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Clear Editor", command=self._clear_editor).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Load from File", command=self._load_file_to_editor).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Save to File", command=self._save_editor_to_file).pack(side=tk.LEFT, padx=5)
        
        # Error display
        error_frame = ttk.LabelFrame(frame, text="Assembly Errors")
        error_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.error_display = scrolledtext.ScrolledText(error_frame, wrap=tk.WORD, height=5, font=("Courier", 10))
        self.error_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.error_display.config(state=tk.DISABLED)
        
        # Assembled instructions display
        asm_frame = ttk.LabelFrame(frame, text="Assembled Instructions")
        asm_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.asm_display = scrolledtext.ScrolledText(asm_frame, wrap=tk.NONE, height=10, font=("Courier", 10))
        self.asm_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.asm_display.config(state=tk.DISABLED)
    
    def _setup_simulator_tab(self):
        """Setup the main simulator tab."""
        frame = ttk.Frame(self.simulator_tab)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Control panel
        control_frame = ttk.LabelFrame(frame, text="Controls")
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Buttons row
        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.step_btn = ttk.Button(btn_frame, text="Step", command=self._step)
        self.step_btn.pack(side=tk.LEFT, padx=5)
        
        self.run_btn = ttk.Button(btn_frame, text="Run", command=self._run)
        self.run_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(btn_frame, text="Stop", command=self._stop, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        self.reset_btn = ttk.Button(btn_frame, text="Reset", command=self._reset)
        self.reset_btn.pack(side=tk.LEFT, padx=5)
        
        # Speed control
        speed_frame = ttk.Frame(control_frame)
        speed_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(speed_frame, text="Cycle Delay (s):").pack(side=tk.LEFT, padx=5)
        speed_scale = ttk.Scale(speed_frame, from_=0.0, to=2.0, orient=tk.HORIZONTAL, 
                               variable=self.cycle_delay, length=200)
        speed_scale.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Status panel
        status_frame = ttk.LabelFrame(frame, text="Status")
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Status grid
        status_grid = ttk.Frame(status_frame)
        status_grid.pack(fill=tk.X, padx=5, pady=5)
        
        # Row 1
        ttk.Label(status_grid, text="Cycle:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.cycle_label = ttk.Label(status_grid, text="0")
        self.cycle_label.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(status_grid, text="PC:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=2)
        self.pc_label = ttk.Label(status_grid, text="0x00000000")
        self.pc_label.grid(row=0, column=3, sticky=tk.W, padx=5, pady=2)
        
        # Row 2
        ttk.Label(status_grid, text="Flags:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.flags_label = ttk.Label(status_grid, text="Z=0 N=0 C=0 V=0")
        self.flags_label.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(status_grid, text="Stalls:").grid(row=1, column=2, sticky=tk.W, padx=5, pady=2)
        self.stalls_label = ttk.Label(status_grid, text="0")
        self.stalls_label.grid(row=1, column=3, sticky=tk.W, padx=5, pady=2)
        
        # Row 3 - Add Cycle Delay display
        ttk.Label(status_grid, text="Cycle Delay:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.cycle_delay_label = ttk.Label(status_grid, text=f"{int(self.cycle_delay.get() * 1000)} ms")
        self.cycle_delay_label.grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)

        def on_cycle_delay_change(*args):
            delay_ms = int(self.cycle_delay.get() * 1000)
            self.cycle_delay_label.config(text=f"{delay_ms} ms")

        self.cycle_delay.trace_add("write", on_cycle_delay_change)

        # Console output
        console_frame = ttk.LabelFrame(frame, text="Console Output")
        console_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.console = scrolledtext.ScrolledText(console_frame, wrap=tk.WORD, height=10)
        self.console.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.console.config(state=tk.DISABLED)
        
        # Pipeline visualization
        pipeline_frame = ttk.LabelFrame(frame, text="Pipeline Status")
        pipeline_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Pipeline stages
        stages_frame = ttk.Frame(pipeline_frame)
        stages_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Create pipeline stage labels
        stage_names = ["Fetch", "Decode", "Execute", "Memory", "Writeback"]
        self.stage_labels = []
        
        for i, stage in enumerate(stage_names):
            frame = ttk.LabelFrame(stages_frame, text=stage)
            frame.grid(row=0, column=i, padx=5, pady=5, sticky=tk.NSEW)
            
            label = ttk.Label(frame, text="---", width=15)
            label.pack(padx=5, pady=5)
            self.stage_labels.append(label)
        
        # Configure grid to expand evenly
        for i in range(5):
            stages_frame.columnconfigure(i, weight=1)
    
    def _setup_registers_tab(self):
        """Setup the registers visualization tab with automatic register tracking."""
        frame = ttk.Frame(self.registers_tab)
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create a frame for register display
        reg_frame = ttk.LabelFrame(frame, text="General Purpose Registers")
        reg_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create register display grid
        self.reg_labels = []
        for i in range(32):
            row = i // 4
            col = i % 4
            
            reg_frame_item = ttk.Frame(reg_frame)
            reg_frame_item.grid(row=row, column=col, padx=5, pady=2, sticky=tk.W)
            
            ttk.Label(reg_frame_item, text=f"R{i}:").pack(side=tk.LEFT)
            label = ttk.Label(reg_frame_item, text="0x00000000", width=12)
            label.pack(side=tk.LEFT)
            self.reg_labels.append(label)
        
        # Create a frame for register history plot
        plot_frame = ttk.LabelFrame(frame, text="Register History")
        plot_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create matplotlib figure for register history
        self.reg_fig = Figure(figsize=(6, 4), dpi=100)
        self.reg_ax = self.reg_fig.add_subplot(111)
        self.reg_ax.set_title("Register Values Over Time")
        self.reg_ax.set_xlabel("Cycle")
        self.reg_ax.set_ylabel("Value")
        
        # Create canvas for the figure
        self.reg_canvas = FigureCanvasTkAgg(self.reg_fig, master=plot_frame)
        self.reg_canvas.draw()
        self.reg_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Add info label and refresh button
        control_frame = ttk.Frame(plot_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(control_frame, text="Register plot automatically shows all used registers").pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Refresh Plot", command=self._update_reg_plot).pack(side=tk.RIGHT, padx=5)
    
    def _setup_memory_tab(self):
        """Setup the memory visualization tab."""
        frame = ttk.Frame(self.memory_tab)
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Memory dump controls
        control_frame = ttk.Frame(frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(control_frame, text="Start Address:").pack(side=tk.LEFT, padx=5)
        self.mem_addr_var = tk.StringVar(value="0x00000000")
        addr_entry = ttk.Entry(control_frame, textvariable=self.mem_addr_var, width=12)
        addr_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(control_frame, text="Length (bytes):").pack(side=tk.LEFT, padx=5)
        self.mem_len_var = tk.StringVar(value="64")
        len_entry = ttk.Entry(control_frame, textvariable=self.mem_len_var, width=8)
        len_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(control_frame, text="Dump Memory", command=self._dump_memory).pack(side=tk.LEFT, padx=5)
        
        # Memory display
        mem_frame = ttk.LabelFrame(frame, text="Memory Dump")
        mem_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.mem_display = scrolledtext.ScrolledText(mem_frame, wrap=tk.NONE, font=("Courier", 10))
        self.mem_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Memory access pattern visualization
        plot_frame = ttk.LabelFrame(frame, text="Memory Access Pattern")
        plot_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create matplotlib figure for memory access
        self.mem_fig = Figure(figsize=(6, 4), dpi=100)
        self.mem_ax = self.mem_fig.add_subplot(111)
        self.mem_ax.set_title("Memory Access Pattern")
        self.mem_ax.set_xlabel("Address")
        self.mem_ax.set_ylabel("Access Count")
        
        # Create canvas for the figure
        self.mem_canvas = FigureCanvasTkAgg(self.mem_fig, master=plot_frame)
        self.mem_canvas.draw()
        self.mem_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def _setup_pipeline_tab(self):
        """Setup the pipeline visualization tab."""
        frame = ttk.Frame(self.pipeline_tab)
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Pipeline registers display
        reg_frame = ttk.LabelFrame(frame, text="Pipeline Registers")
        reg_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Create pipeline register displays
        pipeline_regs = ["IF/ID", "ID/EX", "EX/MEM", "MEM/WB"]
        self.pipeline_text = {}
        
        for i, reg_name in enumerate(pipeline_regs):
            reg_label_frame = ttk.LabelFrame(reg_frame, text=reg_name)
            reg_label_frame.grid(row=0, column=i, padx=5, pady=5, sticky=tk.NSEW)
            
            reg_text = scrolledtext.ScrolledText(reg_label_frame, wrap=tk.WORD, width=25, height=10)
            reg_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            self.pipeline_text[reg_name] = reg_text
        
        # Configure grid to expand evenly
        for i in range(4):
            reg_frame.columnconfigure(i, weight=1)
        
        # Pipeline activity visualization
        plot_frame = ttk.LabelFrame(frame, text="Pipeline Activity")
        plot_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create matplotlib figure for pipeline activity
        self.pipe_fig = Figure(figsize=(6, 4), dpi=100)
        self.pipe_ax = self.pipe_fig.add_subplot(111)
        self.pipe_ax.set_title("Pipeline Activity")
        self.pipe_ax.set_xlabel("Cycle")
        self.pipe_ax.set_ylabel("Pipeline Stage")
        
        # Create canvas for the figure
        self.pipe_canvas = FigureCanvasTkAgg(self.pipe_fig, master=plot_frame)
        self.pipe_canvas.draw()
        self.pipe_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Add button to display pipeline history table
        ttk.Button(plot_frame, text="Show Pipeline History Table", 
                  command=self.display_pipeline_history).pack(pady=5)
    
    def _setup_stats_tab(self):
        """Setup the statistics visualization tab."""
        frame = ttk.Frame(self.stats_tab)
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Performance metrics
        metrics_frame = ttk.LabelFrame(frame, text="Performance Metrics")
        metrics_frame.pack(fill=tk.X, padx=5, pady=5)
        
        metrics_grid = ttk.Frame(metrics_frame)
        metrics_grid.pack(fill=tk.X, padx=5, pady=5)
        
        # Row 1
        ttk.Label(metrics_grid, text="Total Cycles:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.total_cycles_label = ttk.Label(metrics_grid, text="0")
        self.total_cycles_label.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(metrics_grid, text="Instructions Executed:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=2)
        self.instr_exec_label = ttk.Label(metrics_grid, text="0")
        self.instr_exec_label.grid(row=0, column=3, sticky=tk.W, padx=5, pady=2)
        
        # Row 2
        ttk.Label(metrics_grid, text="Stall Cycles:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.stall_cycles_label = ttk.Label(metrics_grid, text="0")
        self.stall_cycles_label.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(metrics_grid, text="IPC:").grid(row=1, column=2, sticky=tk.W, padx=5, pady=2)
        self.ipc_label = ttk.Label(metrics_grid, text="0.00")
        self.ipc_label.grid(row=1, column=3, sticky=tk.W, padx=5, pady=2)
        
        # Instruction mix visualization
        instr_frame = ttk.LabelFrame(frame, text="Instruction Mix")
        instr_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create matplotlib figure for instruction mix
        self.instr_fig = Figure(figsize=(6, 4), dpi=100)
        self.instr_ax = self.instr_fig.add_subplot(111)
        self.instr_ax.set_title("Instruction Type Distribution")
        
        # Create canvas for the figure
        self.instr_canvas = FigureCanvasTkAgg(self.instr_fig, master=instr_frame)
        self.instr_canvas.draw()
        self.instr_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def _assemble_from_editor(self):
        """Assemble and load instructions from the editor."""
        # Get assembly code from editor
        assembly_code = self.instruction_editor.get(1.0, tk.END)
        
        # Clear error and assembly displays
        self._clear_error_display()
        self._clear_asm_display()
        
        # Assemble the code
        try:
            instructions = self.simulator.assembler.assemble(assembly_code)
            
            if instructions is None:
                # Display assembly errors
                self._display_assembly_errors(self.simulator.assembler.errors)
                return
            
            # Display assembled instructions
            self._display_assembled_instructions(instructions)
            
            # Load program into simulator
            self.simulator.load_program(instructions)
            self._log_to_console("Program loaded from editor.")
            
            # Switch to simulator tab
            self.notebook.select(1)  # Index 1 is the simulator tab
            
        except Exception as e:
            self._display_error(f"Assembly error: {str(e)}")
    
    def _clear_editor(self):
        """Clear the instruction editor."""
        self.instruction_editor.delete(1.0, tk.END)
    
    def _load_file_to_editor(self):
        """Load assembly code from a file into the editor."""
        filename = filedialog.askopenfilename(
            title="Open Assembly File",
            filetypes=[("Assembly files", "*.asm"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r') as f:
                    code = f.read()
                    self.instruction_editor.delete(1.0, tk.END)
                    self.instruction_editor.insert(tk.END, code)
                self._log_to_console(f"Loaded file: {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Could not open file: {str(e)}")
    
    def _save_editor_to_file(self):
        """Save the editor content to a file."""
        filename = filedialog.asksaveasfilename(
            title="Save Assembly File",
            defaultextension=".asm",
            filetypes=[("Assembly files", "*.asm"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    code = self.instruction_editor.get(1.0, tk.END)
                    f.write(code)
                self._log_to_console(f"Saved to file: {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Could not save file: {str(e)}")
    
    def _clear_error_display(self):
        """Clear the error display."""
        self.error_display.config(state=tk.NORMAL)
        self.error_display.delete(1.0, tk.END)
        self.error_display.config(state=tk.DISABLED)
    
    def _clear_asm_display(self):
        """Clear the assembled instructions display."""
        self.asm_display.config(state=tk.NORMAL)
        self.asm_display.delete(1.0, tk.END)
        self.asm_display.config(state=tk.DISABLED)
    
    def _display_error(self, error_message):
        """Display an error message in the error display."""
        self.error_display.config(state=tk.NORMAL)
        self.error_display.delete(1.0, tk.END)
        self.error_display.insert(tk.END, error_message)
        self.error_display.config(state=tk.DISABLED)
    
    def _display_assembly_errors(self, errors):
        """Display assembly errors in the error display."""
        self.error_display.config(state=tk.NORMAL)
        self.error_display.delete(1.0, tk.END)
        
        if errors:
            for error in errors:
                self.error_display.insert(tk.END, f"{error}\n")
        else:
            self.error_display.insert(tk.END, "Unknown assembly error.")
        
        self.error_display.config(state=tk.DISABLED)
    
    def _display_assembled_instructions(self, instructions):
        """Display assembled instructions in the assembly display."""
        self.asm_display.config(state=tk.NORMAL)
        self.asm_display.delete(1.0, tk.END)
        
        for i, instr in enumerate(instructions):
            disasm = self.simulator.assembler.disassemble(instr)
            self.asm_display.insert(tk.END, f"0x{i*4:04x}: 0x{instr:08X} - {disasm}\n")
        
        self.asm_display.config(state=tk.DISABLED)
    
    def _update_used_registers(self):
        """Update the set of registers that have been used."""
        # Check all pipeline registers for register usage
        for pipeline_reg_name in ['if_id', 'id_ex', 'ex_mem', 'mem_wb']:
            pipeline_reg = getattr(self.simulator, pipeline_reg_name)
            if pipeline_reg.data:
                if 'dest_reg' in pipeline_reg.data:
                    dest_reg = pipeline_reg.data['dest_reg']
                    if 0 <= dest_reg < 32:
                        self.used_registers.add(dest_reg)
                
                if 'src1_reg' in pipeline_reg.data:
                    src1_reg = pipeline_reg.data['src1_reg']
                    if 0 <= src1_reg < 32:
                        self.used_registers.add(src1_reg)
                
                if 'src2_reg' in pipeline_reg.data:
                    src2_reg = pipeline_reg.data['src2_reg']
                    if 0 <= src2_reg < 32:
                        self.used_registers.add(src2_reg)
        
        # Also check for non-zero values in registers
        for i, value in enumerate(self.simulator.reg_file.registers):
            if value != 0:
                self.used_registers.add(i)
    
    def _step(self):
        halt_in_writeback = False
        if self.simulator.mem_wb.read("instruction") is not None:
            opcode = (self.simulator.mem_wb.read("instruction") >> 24) & 0xFF
            if opcode == self.simulator.control_unit.HALT:
                halt_in_writeback = True

        if not halt_in_writeback:
            self._record_state()  # Record before step
            self.simulator.step()
            self._update_used_registers()
            self._update_display()
            self._log_to_console(f"Cycle {self.simulator.cycles}: PC = 0x{self.simulator.reg_file.pc:08X}")
        else:
            self._record_state()  # Record final state with HALT in writeback
            self._update_display()
            self._log_to_console("Simulation halted (HALT reached writeback stage).")
            self._stop()
    
    def _run(self):
        """Run the simulation continuously."""
        self.running = True
        self.step_btn.config(state=tk.DISABLED)
        self.run_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        
        self._run_cycle()
    
    def _run_cycle(self):
        """Execute a cycle and schedule the next one if still running."""
        if self.running and not self.simulator.control_unit.halt_flag:
            self._step()
            delay_ms = int(self.cycle_delay.get() * 1000)  # Convert to milliseconds
            self.root.after(delay_ms, self._run_cycle)
        else:
            self._stop()
    
    def _stop(self):
        """Stop the continuous simulation."""
        self.running = False
        self.step_btn.config(state=tk.NORMAL)
        self.run_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
    
    def _reset(self):
        """Reset the simulator state."""
        # Create a new simulator instance
        from simulator import ISASimulator
        from assembler import Assembler
        
        self.simulator = ISASimulator(debug=True)
        self.simulator.assembler = Assembler()  # Add assembler to simulator for disassembly
        
        # Clear state history
        self.state_history = []
        
        # Reset cycle counter
        self.simulator.cycles = 0
        
        # Reset used registers
        self.used_registers = set()
        
        # Update display
        self._update_display()
        
        # Clear console
        self.console.config(state=tk.NORMAL)
        self.console.delete(1.0, tk.END)
        self.console.config(state=tk.DISABLED)
        
        self._log_to_console("Simulator reset.")
    
    def _record_state(self):
        """Record the current state of the simulator for history tracking."""
        state = {
            'cycle': self.simulator.cycles,
            'pc': self.simulator.reg_file.pc,
            'registers': self.simulator.reg_file.registers.copy(),
            'flags': {
                'zero': self.simulator.reg_file.zero_flag,
                'negative': self.simulator.reg_file.negative_flag,
                'carry': self.simulator.reg_file.carry_flag,
                'overflow': self.simulator.reg_file.overflow_flag
            },
            'pipeline': {
                'if_id': self.simulator.if_id.data.copy() if self.simulator.if_id.data else {},
                'id_ex': self.simulator.id_ex.data.copy() if self.simulator.id_ex.data else {},
                'ex_mem': self.simulator.ex_mem.data.copy() if self.simulator.ex_mem.data else {},
                'mem_wb': self.simulator.mem_wb.data.copy() if self.simulator.mem_wb.data else {}
            }
        }
        self.state_history.append(state)
    
    def _update_display(self):
        """Update all display elements with current simulator state."""
        # Update status labels
        self.cycle_label.config(text=str(self.simulator.cycles))
        self.pc_label.config(text=f"0x{self.simulator.reg_file.pc:08X}")
        
        flags_text = f"Z={int(self.simulator.reg_file.zero_flag)} " \
                    f"N={int(self.simulator.reg_file.negative_flag)} " \
                    f"C={int(self.simulator.reg_file.carry_flag)} " \
                    f"V={int(self.simulator.reg_file.overflow_flag)}"
        self.flags_label.config(text=flags_text)
        
        self.stalls_label.config(text=str(self.simulator.stall_cycles))
        
        # Update register display
        for i in range(32):
            value = self.simulator.reg_file.registers[i]
            self.reg_labels[i].config(text=f"0x{value:08X}")
        
        # Update pipeline registers display
        self._update_pipeline_display()
        
        # Update performance metrics
        self.total_cycles_label.config(text=str(self.simulator.cycles))
        self.instr_exec_label.config(text=str(self.simulator.instructions_executed))
        self.stall_cycles_label.config(text=str(self.simulator.stall_cycles))
        
        ipc = self.simulator.instructions_executed / max(1, self.simulator.cycles)
        self.ipc_label.config(text=f"{ipc:.2f}")
        
        # Update pipeline stage labels
        self._update_pipeline_stages()
        
        # Update register plot if we're on the registers tab
        if self.notebook.index(self.notebook.select()) == 2:  # Registers tab (index 2 now)
            self._update_reg_plot()
    
    def _update_reg_plot(self):
        """Update the register history plot with all used registers."""
        if not self.state_history:
            return
        
        self.reg_ax.clear()
        self.reg_ax.set_title("Register Values Over Time")
        self.reg_ax.set_xlabel("Cycle")
        self.reg_ax.set_ylabel("Value")
        
        cycles = [state['cycle'] for state in self.state_history]
        
        # Plot all used registers
        for reg_num in sorted(self.used_registers):
            if reg_num < 32:  # Ensure it's a valid register
                values = [state['registers'][reg_num] for state in self.state_history]
                self.reg_ax.plot(cycles, values, label=f"R{reg_num}")
        
        # Add legend with reasonable size and position
        if self.used_registers:
            # If there are many registers, use a smaller font
            legend_font_size = max(6, min(9, 12 - len(self.used_registers) // 4))
            self.reg_ax.legend(fontsize=legend_font_size, loc='upper left', 
                              bbox_to_anchor=(1.01, 1), borderaxespad=0)
        
        self.reg_fig.tight_layout()
        self.reg_canvas.draw()
    
    def _update_pipeline_display(self):
        """Update the pipeline registers display."""
        pipeline_regs = {
            "IF/ID": self.simulator.if_id.data,
            "ID/EX": self.simulator.id_ex.data,
            "EX/MEM": self.simulator.ex_mem.data,
            "MEM/WB": self.simulator.mem_wb.data
        }
        
        for reg_name, reg_data in pipeline_regs.items():
            text_widget = self.pipeline_text[reg_name]
            text_widget.config(state=tk.NORMAL)
            text_widget.delete(1.0, tk.END)
            
            if reg_data:
                for key, value in reg_data.items():
                    if isinstance(value, dict):
                        text_widget.insert(tk.END, f"{key}:\n")
                        for k, v in value.items():
                            text_widget.insert(tk.END, f"  {k}: {v}\n")
                    else:
                        if key == "instruction" and value is not None:
                            # Try to disassemble the instruction
                            try:
                                disasm = self.simulator.assembler.disassemble(value)
                                text_widget.insert(tk.END, f"{key}: 0x{value:08X}\n  {disasm}\n")
                            except:
                                text_widget.insert(tk.END, f"{key}: 0x{value:08X}\n")
                        elif key == "pc" and value is not None:
                            text_widget.insert(tk.END, f"{key}: 0x{value:08X}\n")
                        else:
                            text_widget.insert(tk.END, f"{key}: {value}\n")
            else:
                text_widget.insert(tk.END, "Empty")
            
            text_widget.config(state=tk.DISABLED)
    
    def _update_pipeline_stages(self):
        """Update the pipeline stage labels with current instructions."""
        # Get the current cycle's pipeline state
        if not self.simulator.pipeline_stages:
            return
        
        current_state = self.simulator.pipeline_stages[-1]
        stages = ["Fetch", "Decode", "Execute", "Memory", "Writeback"]
        stage_keys = ["fetch", "decode", "execute", "memory", "writeback"]
        
        for i, (stage, key) in enumerate(zip(stages, stage_keys)):
            label = self.stage_labels[i]
            instr = current_state[key]
            
            if instr is None:
                label.config(text="---")
            else:
                try:
                    disasm = self.simulator.assembler.disassemble(instr)
                    label.config(text=disasm)
                except:
                    label.config(text="---")
    
    def display_pipeline_history(self):
        """Display the pipeline history as a table."""
        if not self.simulator.pipeline_stages:
            messagebox.showinfo("Pipeline History", "No pipeline history available.")
            return
        
        # Create a new window for the pipeline history
        history_window = tk.Toplevel(self.root)
        history_window.title("Pipeline History")
        history_window.geometry("800x600")
        
        # Create a frame for the table
        frame = ttk.Frame(history_window)
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create a scrolled text widget for the table
        text = scrolledtext.ScrolledText(frame, wrap=tk.NONE, font=("Courier", 10))
        text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create the table header
        header = "| Cycle | Fetch | Decode | Execute | Memory | Writeback |\n"
        header += "| ----- | ----- | ------ | ------- | ------ | --------- |\n"
        text.insert(tk.END, header)
        
        # Add each cycle's pipeline state to the table
        for i, state in enumerate(self.simulator.pipeline_stages, 1):
            row = f"| {i} | "
            for stage in ["fetch", "decode", "execute", "memory", "writeback"]:
                instr = state[stage]
                if instr is None:
                    row += "--- | "
                else:
                    try:
                        disasm = self.simulator.assembler.disassemble(instr)
                        row += f"{disasm} | "
                    except:
                        row += "--- | "
            row += "\n"
            text.insert(tk.END, row)
        
        # Add a button to export the table
        ttk.Button(frame, text="Export to File", 
                  command=lambda: self._export_pipeline_history(text.get(1.0, tk.END))).pack(pady=5)

    def _export_pipeline_history(self, content):
        """Export the pipeline history to a file."""
        filename = filedialog.asksaveasfilename(
            title="Export Pipeline History",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write(content)
                messagebox.showinfo("Export Successful", f"Pipeline history exported to {filename}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Could not export file: {str(e)}")
    
    def _dump_memory(self):
        """Dump memory contents to the memory display."""
        try:
            # Parse address and length
            addr_str = self.mem_addr_var.get()
            if addr_str.startswith("0x"):
                start_address = int(addr_str, 16)
            else:
                start_address = int(addr_str)
            
            length = int(self.mem_len_var.get())
            
            # Clear display
            self.mem_display.config(state=tk.NORMAL)
            self.mem_display.delete(1.0, tk.END)
            
            # Add header
            self.mem_display.insert(tk.END, "Address    | Value (hex) | Value (dec) | ASCII\n")
            self.mem_display.insert(tk.END, "-" * 60 + "\n")
            
            # Dump memory
            end_address = start_address + length
            for addr in range(start_address, end_address, 4):
                try:
                    value = self.simulator.memory.read_word(addr)
                    
                    # Try to interpret as ASCII
                    ascii_repr = ""
                    for i in range(4):
                        byte_val = (value >> (i * 8)) & 0xFF
                        if 32 <= byte_val <= 126:  # Printable ASCII
                            ascii_repr += chr(byte_val)
                        else:
                            ascii_repr += "."
                    
                    line = f"0x{addr:08X} | 0x{value:08X} | {value:10} | {ascii_repr}\n"
                    self.mem_display.insert(tk.END, line)
                except Exception as e:
                    self.mem_display.insert(tk.END, f"0x{addr:08X} | Error: {str(e)}\n")
            
            self.mem_display.config(state=tk.DISABLED)
            
        except ValueError as e:
            self.mem_display.config(state=tk.NORMAL)
            self.mem_display.delete(1.0, tk.END)
            self.mem_display.insert(tk.END, f"Error: {str(e)}")
            self.mem_display.config(state=tk.DISABLED)
    
    def _log_to_console(self, message):
        """Log a message to the console display."""
        self.console.config(state=tk.NORMAL)
        self.console.insert(tk.END, message + "\n")
        self.console.see(tk.END)
        self.console.config(state=tk.DISABLED)
    
    def load_program(self, instructions):
        """Load a program into the simulator."""
        self.simulator.load_program(instructions)
        self._log_to_console("Program loaded.")
        self._update_display()
    
    def update_pipeline_activity_plot(self):
        """Update the pipeline activity visualization."""
        if len(self.state_history) < 2:
            return
        
        self.pipe_ax.clear()
        self.pipe_ax.set_title("Pipeline Activity")
        self.pipe_ax.set_xlabel("Cycle")
        self.pipe_ax.set_ylabel("Pipeline Stage")
        
        # Create a colormap for different instruction types
        stages = ["Fetch", "Decode", "Execute", "Memory", "Writeback"]
        cycles = range(len(self.state_history))
        
        # Create a matrix of activity (1 for active, 0 for inactive)
        activity = np.zeros((5, len(cycles)))
        
        # Fill in the activity matrix based on state history
        # This is a simplified version - in a real implementation you'd
        # track which instructions are in which stages
        for i, state in enumerate(self.state_history):
            # Fetch is active if not stalled
            activity[0, i] = 1 if not self.simulator.stall else 0
            
            # Other stages are active if their input pipeline register has data
            pipeline_regs = [
                state['pipeline']['if_id'],
                state['pipeline']['id_ex'],
                state['pipeline']['ex_mem'],
                state['pipeline']['mem_wb']
            ]
            
            for j, reg in enumerate(pipeline_regs):
                activity[j+1, i] = 1 if reg else 0
        
        # Plot the activity matrix as a heatmap
        im = self.pipe_ax.imshow(activity, aspect='auto', cmap='viridis')
        
        # Set y-ticks to stage names
        self.pipe_ax.set_yticks(range(5))
        self.pipe_ax.set_yticklabels(stages)
        
        # Set x-ticks to cycle numbers
        self.pipe_ax.set_xticks(range(0, len(cycles), max(1, len(cycles)//10)))
        
        self.pipe_fig.tight_layout()
        self.pipe_canvas.draw()
    
    def update_instruction_mix_plot(self):
        """Update the instruction mix visualization."""
        if not self.state_history:
            return
        
        self.instr_ax.clear()
        self.instr_ax.set_title("Instruction Type Distribution")
        
        # Count instruction types
        instr_types = {}
        
        for state in self.state_history:
            for reg_name in ['if_id', 'id_ex', 'ex_mem', 'mem_wb']:
                reg_data = state['pipeline'][reg_name]
                if reg_data and 'opcode' in reg_data:
                    opcode = reg_data['opcode']
                    
                    # Determine instruction type from opcode
                    if 0x00 <= opcode <= 0x1F:
                        instr_type = "Data Processing"
                    elif 0x20 <= opcode <= 0x3F:
                        instr_type = "Memory Access"
                    elif 0x40 <= opcode <= 0x5F:
                        instr_type = "Control Flow"
                    elif 0x60 <= opcode <= 0x7F:
                        instr_type = "System Ops"
                    else:
                        instr_type = "Unknown"
                    
                    instr_types[instr_type] = instr_types.get(instr_type, 0) + 1
        
        if instr_types:
            # Plot as pie chart
            labels = list(instr_types.keys())
            sizes = list(instr_types.values())
            
            self.instr_ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
            self.instr_ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
            
            self.instr_fig.tight_layout()
            self.instr_canvas.draw()