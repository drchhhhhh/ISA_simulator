import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox

# Import simulator components
from core.register_file import RegisterFile
from core.memory import Memory
from core.alu import ALU
from core.control_unit import ControlUnit
from core.pipeline_register import PipelineRegister
from simulator import ISASimulator
from assembler import Assembler
from visualization.visualizer import ISASimulatorGUI

def load_assembly_file(filename):
    """Load assembly code from a file."""
    try:
        with open(filename, 'r') as f:
            return f.read()
    except FileNotFoundError:
        return None

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
    
    # Add menu bar
    menubar = tk.Menu(root)
    
    # File menu
    file_menu = tk.Menu(menubar, tearoff=0)
    file_menu.add_command(label="Open Assembly File", command=lambda: open_file(gui, simulator))
    file_menu.add_separator()
    file_menu.add_command(label="Exit", command=root.quit)
    menubar.add_cascade(label="File", menu=file_menu)
    
    # View menu
    view_menu = tk.Menu(menubar, tearoff=0)
    view_menu.add_command(label="Update Register Plot", command=gui._update_reg_plot)
    view_menu.add_command(label="Update Pipeline Activity", command=gui.update_pipeline_activity_plot)
    view_menu.add_command(label="Update Instruction Mix", command=gui.update_instruction_mix_plot)
    menubar.add_cascade(label="View", menu=view_menu)
    
    # Help menu
    help_menu = tk.Menu(menubar, tearoff=0)
    help_menu.add_command(label="About", command=lambda: messagebox.showinfo("About", "ISA Simulator\nA visual simulator for a simple instruction set architecture."))
    menubar.add_cascade(label="Help", menu=help_menu)
    
    root.config(menu=menubar)
    
    # Register callback for console output
    def console_output_callback(char):
        gui._log_to_console(f"Console output: '{char}'")
    
    simulator.memory.register_io_callback('console_out', console_output_callback)
    
    # Check command line arguments for assembly file
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        assembly_code = load_assembly_file(filename)
        if assembly_code:
            load_program(gui, simulator, assembly_code, filename)
    
    # Start the main loop
    root.mainloop()

def open_file(gui, simulator):
    """Open an assembly file and load it into the simulator."""
    filename = filedialog.askopenfilename(
        title="Open Assembly File",
        filetypes=[("Assembly files", "*.asm"), ("All files", "*.*")]
    )
    
    if filename:
        assembly_code = load_assembly_file(filename)
        if assembly_code:
            load_program(gui, simulator, assembly_code, filename)
        else:
            messagebox.showerror("Error", f"Could not open file: {filename}")

def load_program(gui, simulator, assembly_code, filename):
    """Assemble and load a program into the simulator."""
    # Assemble the program
    gui._log_to_console(f"Assembling program from {filename}...")
    instructions = simulator.assembler.assemble(assembly_code)
    
    if instructions is None:
        gui._log_to_console("Assembly failed. Check errors.")
        return
    
    # Print the assembled instructions
    gui._log_to_console("\nAssembled instructions:")
    for i, instr in enumerate(instructions):
        disasm = simulator.assembler.disassemble(instr)
        gui._log_to_console(f"0x{i*4:04x}: 0x{instr:08X} - {disasm}")
    
    # Load program into simulator
    gui._log_to_console("\nLoading program...")
    gui.load_program(instructions)
    gui._log_to_console("Program loaded successfully.")

if __name__ == "__main__":
    main()