import tkinter as tk
from tkinter import ttk, scrolledtext
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
import time

class ISASimulatorGUI:
    """Tkinter-based GUI for the ISA Simulator."""
    
    def __init__(self, root, simulator):
        self.root = root
        self.simulator = simulator
        self.root.title("ISA Simulator")
        self.root.geometry("1200x800")
        
        # Setup control variables - MOVED THESE UP BEFORE USING THEM
        self.running = False
        self.cycle_delay = tk.DoubleVar(value=0.5)  # seconds between cycles
        
        # Create main frame
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self.simulator_tab = ttk.Frame(self.notebook)
        self.registers_tab = ttk.Frame(self.notebook)
        self.memory_tab = ttk.Frame(self.notebook)
        self.pipeline_tab = ttk.Frame(self.notebook)
        self.stats_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.simulator_tab, text="Simulator")
        self.notebook.add(self.registers_tab, text="Registers")
        self.notebook.add(self.memory_tab, text="Memory")
        self.notebook.add(self.pipeline_tab, text="Pipeline")
        self.notebook.add(self.stats_tab, text="Statistics")
        
        # Setup each tab
        self._setup_simulator_tab()
        self._setup_registers_tab()
        self._setup_memory_tab()
        self._setup_pipeline_tab()
        self._setup_stats_tab()
        
        # Initialize state history
        self.state_history = []
        
        # Register update function
        self.root.after(100, self._update_display)
    
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
        """Setup the registers visualization tab."""
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
        
        # Register selection for plotting
        select_frame = ttk.Frame(plot_frame)
        select_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(select_frame, text="Select registers to plot:").pack(side=tk.LEFT, padx=5)
        
        self.reg_to_plot = []
        for i in range(4):  # Allow selecting 4 registers to plot
            var = tk.StringVar(value=f"R{i}")
            combo = ttk.Combobox(select_frame, textvariable=var, values=[f"R{j}" for j in range(32)], width=5)
            combo.pack(side=tk.LEFT, padx=5)
            self.reg_to_plot.append(var)
        
        ttk.Button(select_frame, text="Update Plot", command=self._update_reg_plot).pack(side=tk.LEFT, padx=5)
    
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
    
    def _step(self):
        """Execute a single cycle of the simulator."""
        if not self.simulator.control_unit.halt_flag:
            # Record state before step
            self._record_state()
            
            # Execute one cycle
            self.simulator.step()
            
            # Update display
            self._update_display()
            
            # Log to console
            self._log_to_console(f"Cycle {self.simulator.cycles}: PC = 0x{self.simulator.reg_file.pc:08X}")
        else:
            self._log_to_console("Simulation halted.")
    
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
        self.simulator = ISASimulator(debug=True)
        
        # Clear state history
        self.state_history = []
        
        # Reset cycle counter
        self.simulator.cycles = 0
        
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
        # This is a simplified view - in a real implementation you'd extract the actual
        # instructions in each stage from the simulator state
        stages = ["Fetch", "Decode", "Execute", "Memory", "Writeback"]
        pipeline_regs = [
            self.simulator.if_id.data,
            self.simulator.id_ex.data,
            self.simulator.ex_mem.data,
            self.simulator.mem_wb.data,
            {}  # Writeback doesn't have a "next" register
        ]
        
        for i, (stage, reg_data) in enumerate(zip(stages, pipeline_regs)):
            label = self.stage_labels[i]
            
            if i == 0:  # Fetch stage
                if not self.simulator.stall:
                    try:
                        instr = self.simulator.memory.read_word(self.simulator.reg_file.pc)
                        disasm = self.simulator.assembler.disassemble(instr)
                        label.config(text=disasm)
                    except:
                        label.config(text="---")
                else:
                    label.config(text="STALL")
            elif reg_data and "opcode" in reg_data:
                # For other stages, show the instruction based on opcode
                opcode = reg_data["opcode"]
                try:
                    # Create a dummy instruction to disassemble
                    if "dest_reg" in reg_data and "src1_reg" in reg_data:
                        instr = (opcode << 24) | (reg_data["dest_reg"] << 16) | (reg_data["src1_reg"] << 8)
                        if "src2_reg" in reg_data:
                            instr |= reg_data["src2_reg"]
                        disasm = self.simulator.assembler.disassemble(instr)
                        label.config(text=disasm)
                    else:
                        label.config(text=f"OP: 0x{opcode:02X}")
                except:
                    label.config(text=f"OP: 0x{opcode:02X}")
            else:
                label.config(text="---")
    
    def _update_reg_plot(self):
        """Update the register history plot."""
        if not self.state_history:
            return
        
        self.reg_ax.clear()
        self.reg_ax.set_title("Register Values Over Time")
        self.reg_ax.set_xlabel("Cycle")
        self.reg_ax.set_ylabel("Value")
        
        cycles = [state['cycle'] for state in self.state_history]
        
        for reg_var in self.reg_to_plot:
            reg_name = reg_var.get()
            if reg_name.startswith('R'):
                try:
                    reg_num = int(reg_name[1:])
                    if 0 <= reg_num < 32:
                        values = [state['registers'][reg_num] for state in self.state_history]
                        self.reg_ax.plot(cycles, values, label=reg_name)
                except ValueError:
                    pass
        
        self.reg_ax.legend()
        self.reg_fig.tight_layout()
        self.reg_canvas.draw()
    
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