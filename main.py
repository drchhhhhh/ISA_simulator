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

    # Register callback for console output
    def console_output_callback(char):
        gui._log_to_console(f"Console output: '{char}'")
    
    simulator.memory.register_io_callback('console_out', console_output_callback)
    
    # Start the main loop
    root.mainloop()

if __name__ == "__main__":
    main()