import os
import sys
from simulator import ISASimulator
from assembler import Assembler
from visualization.visualizer import SimulationVisualizer

def load_assembly_file(filename):
    """Load assembly code from a file."""
    try:
        with open(filename, 'r') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        return None

def run_simulation(assembly_code, max_cycles=1000, visualize=True, debug=True):
    """Run a simulation with the given assembly code."""
    # Create simulator components
    simulator = ISASimulator(debug=debug)
    assembler = Assembler()
    
    # Assemble the program
    print("Assembling program...")
    instructions = assembler.assemble(assembly_code)
    
    if instructions is None:
        print("Assembly failed. Check errors.")
        return
    
    # Print the assembled instructions
    print("\nAssembled instructions:")
    for i, instr in enumerate(instructions):
        print(f"0x{i*4:04x}: 0x{instr:08x} - {assembler.disassemble(instr)}")
    
    # Load program into simulator
    print("\nLoading program...")
    simulator.load_program(instructions)
    
    # Create visualizer if requested
    visualizer = None
    if visualize:
        visualizer = SimulationVisualizer(simulator)
    
    # Register callback for console output
    def console_output_callback(char):
        print(f"Console output: '{char}'")
    
    simulator.memory.register_io_callback('console_out', console_output_callback)
    
    # Run simulation
    print("\nStarting simulation...")
    
    cycle = 0
    while cycle < max_cycles and not simulator.control_unit.halt_flag:
        # Record state before executing cycle
        if visualizer:
            visualizer.record_state()
        
        # Execute one cycle
        simulator.step()
        
        # Print cycle information
        print(f"Cycle {cycle}: PC = 0x{simulator.reg_file.pc:08X}")
        
        cycle += 1
    
    # Print final register state
    print("\nFinal register state:")
    for i in range(16):  # Print first 16 registers
        print(f"R{i}: {simulator.reg_file.registers[i]} (0x{simulator.reg_file.registers[i]:08X})")
    
    # Print memory at result location
    print("\nResult in memory:")
    simulator.memory.dump_memory(0x10000000, 16)
    
    # Show visualizations if requested
    if visualize and visualizer:
        print("\nGenerating execution trace...")
        visualizer.print_execution_trace()
        
        print("\nGenerating visualizations...")
        visualizer.plot_register_history([1, 2, 3, 4])  # Plot key registers
        visualizer.plot_pipeline_activity()
        visualizer.plot_instruction_mix()
        visualizer.plot_memory_access_pattern()
    
    print("\nSimulation complete!")
    
    return {
        "cycles": simulator.cycles,
        "instructions": simulator.instructions_executed,
        "stalls": simulator.stall_cycles
    }

def main():
    """Main function to run the ISA simulator."""
    # Check command line arguments
    if len(sys.argv) < 2:
        print("Usage: python main.py <assembly_file> [--no-viz]")
        print("Available example files:")
        for filename in os.listdir('examples'):
            if filename.endswith('.asm'):
                print(f"  examples/{filename}")
        return
    
    # Parse arguments
    filename = sys.argv[1]
    visualize = "--no-viz" not in sys.argv
    
    # Load assembly code
    assembly_code = load_assembly_file(filename)
    if assembly_code is None:
        return
    
    # Run simulation
    run_simulation(assembly_code, visualize=visualize)

if __name__ == "__main__":
    main()