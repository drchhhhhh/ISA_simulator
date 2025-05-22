import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# Import simulator components
from core.register_file import RegisterFile
from core.memory import Memory
from core.alu import ALU
from core.control_unit import ControlUnit
from core.pipeline_register import PipelineRegister
from simulator import ISASimulator
from assembler import Assembler
from visualization.visualizer import ISASimulatorGUI

def main():
    """Main function to run the ISA simulator with Tkinter GUI."""
    # Create the root window
    root = tk.Tk()
    root.title("ISA Simulator")
    
    # Create simulator components
    simulator = ISASimulator(debug=True)
    simulator.assembler = Assembler()  # Add assembler to simulator for disassembly
    
    # Create GUI
    gui = ISASimulatorGUI(root, simulator)
    
    # Add register debugger tab
    add_register_debugger_tab(gui, simulator)

    # Register callback for console output
    def console_output_callback(char):
        gui._log_to_console(f"Console output: '{char}'")
    
    simulator.memory.register_io_callback('console_out', console_output_callback)
    
    # Start the main loop
    root.mainloop()

def add_register_debugger_tab(gui, simulator):
    """Add a register debugger tab to the GUI."""
    # Create a new tab for register debugging
    debugger_tab = ttk.Frame(gui.notebook)
    gui.notebook.add(debugger_tab, text="Register Debugger")
    
    # Create a frame for the debugger controls
    control_frame = ttk.LabelFrame(debugger_tab, text="Debugger Controls")
    control_frame.pack(fill=tk.X, padx=5, pady=5)
    
    # Add cycle navigation
    cycle_frame = ttk.Frame(control_frame)
    cycle_frame.pack(fill=tk.X, padx=5, pady=5)
    
    ttk.Label(cycle_frame, text="Cycle:").pack(side=tk.LEFT, padx=5)
    cycle_var = tk.StringVar(value="0")
    cycle_entry = ttk.Entry(cycle_frame, textvariable=cycle_var, width=8)
    cycle_entry.pack(side=tk.LEFT, padx=5)
    
    def show_cycle_registers():
        try:
            cycle = int(cycle_var.get())
            display_cycle_registers(cycle)
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid cycle number")
    
    ttk.Button(cycle_frame, text="Show Registers", command=show_cycle_registers).pack(side=tk.LEFT, padx=5)
    
    # Add register history lookup
    reg_frame = ttk.Frame(control_frame)
    reg_frame.pack(fill=tk.X, padx=5, pady=5)
    
    ttk.Label(reg_frame, text="Register:").pack(side=tk.LEFT, padx=5)
    reg_var = tk.StringVar(value="1")
    reg_entry = ttk.Entry(reg_frame, textvariable=reg_var, width=8)
    reg_entry.pack(side=tk.LEFT, padx=5)
    
    def show_register_history():
        try:
            reg = int(reg_var.get())
            if 0 <= reg < 32:
                display_register_history(reg)
            else:
                messagebox.showerror("Error", "Register number must be between 0 and 31")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid register number")
    
    ttk.Button(reg_frame, text="Show History", command=show_register_history).pack(side=tk.LEFT, padx=5)
    
    # Add export button
    export_frame = ttk.Frame(control_frame)
    export_frame.pack(fill=tk.X, padx=5, pady=5)
    
    def export_register_data():
        filename = filedialog.asksaveasfilename(
            title="Export Register Debug Data",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                simulator.register_debugger.save_to_file(filename)
                messagebox.showinfo("Export Successful", f"Register debug data exported to {filename}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Could not export file: {str(e)}")
    
    ttk.Button(export_frame, text="Export Debug Data", command=export_register_data).pack(side=tk.LEFT, padx=5)
    
    # Create a frame for the register display
    display_frame = ttk.LabelFrame(debugger_tab, text="Register Usage")
    display_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    # Create text widget for register display
    register_display = tk.scrolledtext.ScrolledText(display_frame, wrap=tk.WORD, font=("Courier", 10))
    register_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def display_cycle_registers(cycle):
        """Display register usage for a specific cycle."""
        register_display.config(state=tk.NORMAL)
        register_display.delete(1.0, tk.END)
        
        reg_data = simulator.register_debugger.get_cycle_register_data(cycle)
        if reg_data is None:
            register_display.insert(tk.END, f"No register data for cycle {cycle}")
        else:
            register_display.insert(tk.END, f"===== CYCLE {cycle} REGISTER USAGE =====\n\n")
            
            for stage in ['fetch', 'decode', 'execute', 'memory', 'writeback']:
                regs = reg_data[stage]
                if regs:
                    register_display.insert(tk.END, f"{stage.upper()} STAGE:\n")
                    for reg_num, details in sorted(regs.items()):
                        op = details['operation']
                        value = details['value']
                        register_display.insert(tk.END, f"  R{reg_num}: 0x{value:08X} ({value}) - {op}\n")
                else:
                    register_display.insert(tk.END, f"{stage.upper()} STAGE: No registers used\n")
                
                register_display.insert(tk.END, "\n")
        
        register_display.config(state=tk.DISABLED)
    
    def display_register_history(reg_num):
        """Display the history of a specific register."""
        register_display.config(state=tk.NORMAL)
        register_display.delete(1.0, tk.END)
        
        register_display.insert(tk.END, f"===== REGISTER R{reg_num} HISTORY =====\n\n")
        
        found_any = False
        for cycle in sorted(simulator.register_debugger.register_usage.keys()):
            found_in_cycle = False
            for stage in ['fetch', 'decode', 'execute', 'memory', 'writeback']:
                stage_regs = simulator.register_debugger.register_usage[cycle][stage]
                if reg_num in stage_regs:
                    details = stage_regs[reg_num]
                    op = details['operation']
                    value = details['value']
                    register_display.insert(tk.END, f"Cycle {cycle}, {stage.capitalize()}: 0x{value:08X} ({value}) - {op}\n")
                    found_in_cycle = True
                    found_any = True
            
            if not found_in_cycle:
                register_display.insert(tk.END, f"Cycle {cycle}: Not used\n")
        
        if not found_any:
            register_display.insert(tk.END, f"Register R{reg_num} was not used in any cycle.")
        
        register_display.config(state=tk.DISABLED)
    
    # Update GUI reference to access the register display
    gui.register_display = register_display
    gui.display_cycle_registers = display_cycle_registers


if __name__ == "__main__":
    main()