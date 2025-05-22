class RegisterDebugger:
    """Tracks register usage and values throughout the pipeline execution."""
    
    def __init__(self, simulator):
        self.simulator = simulator
        self.cycle_history = []
        self.current_cycle = 0
        self.enabled = True
        
        # Dictionary to track register usage per stage per cycle
        # Format: {cycle: {stage: {reg_num: value}}}
        self.register_usage = {}
    
    def start_cycle(self, cycle_num):
        """Start tracking a new cycle."""
        self.current_cycle = cycle_num
        self.register_usage[cycle_num] = {
            'fetch': {},
            'decode': {},
            'execute': {},
            'memory': {},
            'writeback': {}
        }
    
    def track_register_read(self, stage, reg_num, value):
        """Track when a register is read in a pipeline stage."""
        if not self.enabled:
            return
            
        if self.current_cycle in self.register_usage:
            if stage in self.register_usage[self.current_cycle]:
                # Only track if not already tracked (to distinguish first use)
                if reg_num not in self.register_usage[self.current_cycle][stage]:
                    self.register_usage[self.current_cycle][stage][reg_num] = {
                        'value': value,
                        'operation': 'read'
                    }
    
    def track_register_write(self, stage, reg_num, value):
        """Track when a register is written in a pipeline stage."""
        if not self.enabled:
            return
            
        if self.current_cycle in self.register_usage:
            if stage in self.register_usage[self.current_cycle]:
                self.register_usage[self.current_cycle][stage][reg_num] = {
                    'value': value,
                    'operation': 'write'
                }
    
    def print_cycle_registers(self, cycle_num=None):
        """Print register usage for a specific cycle or the current cycle."""
        if cycle_num is None:
            cycle_num = self.current_cycle
        
        if cycle_num not in self.register_usage:
            print(f"No register data for cycle {cycle_num}")
            return
        
        print(f"\n===== CYCLE {cycle_num} REGISTER USAGE =====")
        
        for stage in ['fetch', 'decode', 'execute', 'memory', 'writeback']:
            regs = self.register_usage[cycle_num][stage]
            if regs:
                print(f"\n  {stage.upper()} STAGE:")
                for reg_num, details in sorted(regs.items()):
                    op = details['operation']
                    value = details['value']
                    print(f"    R{reg_num}: 0x{value:08X} ({value}) - {op}")
            else:
                print(f"\n  {stage.upper()} STAGE: No registers used")
        
        print("\n=====================================")
    
    def print_register_history(self, reg_num):
        """Print the history of a specific register across all cycles."""
        print(f"\n===== REGISTER R{reg_num} HISTORY =====")
        
        for cycle in sorted(self.register_usage.keys()):
            found = False
            for stage in ['fetch', 'decode', 'execute', 'memory', 'writeback']:
                if reg_num in self.register_usage[cycle][stage]:
                    details = self.register_usage[cycle][stage][reg_num]
                    op = details['operation']
                    value = details['value']
                    print(f"  Cycle {cycle}, {stage.capitalize()}: 0x{value:08X} ({value}) - {op}")
                    found = True
            
            if not found:
                print(f"  Cycle {cycle}: Not used")
        
        print("\n=====================================")
    
    def get_cycle_register_data(self, cycle_num=None):
        """Get register usage data for a specific cycle in a structured format."""
        if cycle_num is None:
            cycle_num = self.current_cycle
        
        if cycle_num not in self.register_usage:
            return None
        
        return self.register_usage[cycle_num]
    
    def save_to_file(self, filename):
        """Save the register usage history to a file."""
        with open(filename, 'w') as f:
            f.write("REGISTER USAGE HISTORY\n")
            f.write("======================\n\n")
            
            for cycle in sorted(self.register_usage.keys()):
                f.write(f"CYCLE {cycle}\n")
                f.write("---------\n")
                
                for stage in ['fetch', 'decode', 'execute', 'memory', 'writeback']:
                    regs = self.register_usage[cycle][stage]
                    if regs:
                        f.write(f"\n  {stage.upper()} STAGE:\n")
                        for reg_num, details in sorted(regs.items()):
                            op = details['operation']
                            value = details['value']
                            f.write(f"    R{reg_num}: 0x{value:08X} ({value}) - {op}\n")
                    else:
                        f.write(f"\n  {stage.upper()} STAGE: No registers used\n")
                
                f.write("\n")
