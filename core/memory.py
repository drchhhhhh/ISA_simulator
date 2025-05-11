class Memory:
    """Simulates a unified memory space with 32-bit addressing and memory-mapped I/O."""
    
    def __init__(self, size_bytes=1024*1024):  # Default 1MB
        self.size = size_bytes
        self.data = bytearray(size_bytes)
        
        # Memory segments
        self.TEXT_START = 0x00000000
        self.DATA_START = 0x10000000
        self.HEAP_START = 0x20000000
        self.STACK_START = 0x30000000
        
        # Memory-mapped I/O
        self.IO_START = 0xFFFF0000  # Start of I/O address space
        
        # I/O device registers
        self.IO_CONSOLE_OUT = 0xFFFF0000  # Write to console
        self.IO_CONSOLE_IN = 0xFFFF0004   # Read from console
        self.IO_DISPLAY_CTRL = 0xFFFF0008 # Display control
        self.IO_KEYBOARD_CTRL = 0xFFFF000C # Keyboard control
        self.IO_TIMER_CTRL = 0xFFFF0010   # Timer control
        self.IO_TIMER_DATA = 0xFFFF0014   # Timer data
        self.IO_INTERRUPT_CTRL = 0xFFFF0018 # Interrupt control
        self.IO_INTERRUPT_STATUS = 0xFFFF001C # Interrupt status
        
        # I/O device buffers and state
        self.io_devices = {
            'console_out_buffer': [],
            'console_in_buffer': [],
            'keyboard_buffer': [],
            'timer_value': 0,
            'timer_enabled': False,
            'interrupt_mask': 0,
            'interrupt_status': 0
        }
        
        # I/O callbacks
        self.io_callbacks = {
            'console_out': None,
            'console_in': None,
            'keyboard': None,
            'timer': None,
            'interrupt': None,
            'display': None
        }
    
    def read_byte(self, address):
        """Read a single byte from memory."""
        if 0 <= address < self.size:
            return self.data[address]
        elif self._is_io_address(address):
            return self._handle_io_read(address, 'byte')
        else:
            raise ValueError(f"Memory access out of bounds: {hex(address)}")
    
    def write_byte(self, address, value):
        """Write a single byte to memory."""
        if 0 <= address < self.size:
            self.data[address] = value & 0xFF
        elif self._is_io_address(address):
            self._handle_io_write(address, value & 0xFF, 'byte')
        else:
            raise ValueError(f"Memory access out of bounds: {hex(address)}")
    
    def read_word(self, address):
        """Read a 32-bit word from memory (little-endian)."""
        if address % 4 != 0:
            raise ValueError(f"Unaligned memory access at address: {hex(address)}")
        
        # Map segment addresses to physical memory
        physical_addr = self._map_address(address)
        
        if 0 <= physical_addr < self.size - 3:
            return (self.data[physical_addr] | 
                (self.data[physical_addr + 1] << 8) | 
                (self.data[physical_addr + 2] << 16) | 
                (self.data[physical_addr + 3] << 24))
        elif self._is_io_address(address):
            return self._handle_io_read(address, 'word')
        else:
            raise ValueError(f"Memory access out of bounds: {hex(address)}")

    def write_word(self, address, value):
        """Write a 32-bit word to memory (little-endian)."""
        if address % 4 != 0:
            raise ValueError(f"Unaligned memory access at address: {hex(address)}")
        
        # Map segment addresses to physical memory
        physical_addr = self._map_address(address)
        
        if 0 <= physical_addr < self.size - 3:
            self.data[physical_addr] = value & 0xFF
            self.data[physical_addr + 1] = (value >> 8) & 0xFF
            self.data[physical_addr + 2] = (value >> 16) & 0xFF
            self.data[physical_addr + 3] = (value >> 24) & 0xFF
        elif self._is_io_address(address):
            self._handle_io_write(address, value, 'word')
        else:
            raise ValueError(f"Memory access out of bounds: {hex(address)}")

    def _map_address(self, address):
        """Map logical address to physical memory address."""
        # Handle data segment (0x10000000-0x1FFFFFFF)
        if self.DATA_START <= address < self.HEAP_START:
            return address - self.DATA_START
        # Handle text segment (0x00000000-0x0FFFFFFF)
        elif self.TEXT_START <= address < self.DATA_START:
            return address
        # Handle heap segment (0x20000000-0x2FFFFFFF)
        elif self.HEAP_START <= address < self.STACK_START:
            return address - self.HEAP_START + (self.DATA_START - self.TEXT_START)
        # Handle stack segment (0x30000000-0x3FFFFFFF)
        elif self.STACK_START <= address < self.IO_START:
            return address - self.STACK_START + (self.HEAP_START - self.TEXT_START) + (self.DATA_START - self.TEXT_START)
        else:
            return address  # For I/O addresses or others
    
    def _is_io_address(self, address):
        """Check if an address is in the memory-mapped I/O range."""
        return address >= self.IO_START
    
    def _handle_io_read(self, address, size):
        """Handle read from memory-mapped I/O device."""
        # Align to word boundary for easier handling
        aligned_addr = address & 0xFFFFFFFC
        
        if aligned_addr == self.IO_CONSOLE_IN:
            return self._read_console_input()
        elif aligned_addr == self.IO_KEYBOARD_CTRL:
            return self._read_keyboard_status()
        elif aligned_addr == self.IO_TIMER_CTRL:
            return int(self.io_devices['timer_enabled'])
        elif aligned_addr == self.IO_TIMER_DATA:
            return self.io_devices['timer_value']
        elif aligned_addr == self.IO_INTERRUPT_STATUS:
            return self.io_devices['interrupt_status']
        elif aligned_addr == self.IO_INTERRUPT_CTRL:
            return self.io_devices['interrupt_mask']
        else:
            print(f"Warning: Read from unmapped I/O address: {hex(address)}")
            return 0
    
    def _handle_io_write(self, address, value, size):
        """Handle write to memory-mapped I/O device."""
        # Align to word boundary for easier handling
        aligned_addr = address & 0xFFFFFFFC
        
        if aligned_addr == self.IO_CONSOLE_OUT:
            self._write_console_output(value)
        elif aligned_addr == self.IO_DISPLAY_CTRL:
            self._update_display(value)
        elif aligned_addr == self.IO_TIMER_CTRL:
            self.io_devices['timer_enabled'] = bool(value & 0x1)
        elif aligned_addr == self.IO_TIMER_DATA:
            self.io_devices['timer_value'] = value
        elif aligned_addr == self.IO_INTERRUPT_CTRL:
            self.io_devices['interrupt_mask'] = value
            self._check_interrupts()
        else:
            print(f"Warning: Write to unmapped I/O address: {hex(address)}")
    
    def _read_console_input(self):
        """Read a character from console input buffer."""
        if self.io_devices['console_in_buffer']:
            return self.io_devices['console_in_buffer'].pop(0)
        return 0  # No input available
    
    def _write_console_output(self, value):
        """Write a character to console output."""
        char = chr(value & 0xFF)
        self.io_devices['console_out_buffer'].append(char)
        
        # Print to console
        print(char, end='', flush=True)
        
        # Call callback if registered
        if self.io_callbacks['console_out']:
            self.io_callbacks['console_out'](char)
    
    def _read_keyboard_status(self):
        """Read keyboard status (1 if key available, 0 otherwise)."""
        return 1 if self.io_devices['keyboard_buffer'] else 0
    
    def _update_display(self, value):
        """Update display control register."""
        # This would typically update a graphical display
        # For simulation, we just print the command
        print(f"Display control updated: 0x{value:08X}")
        
        # Call callback if registered
        if self.io_callbacks['display']:
            self.io_callbacks['display'](value)
    
    def _check_interrupts(self):
        """Check and handle pending interrupts."""
        # Calculate active interrupts (status AND mask)
        active_interrupts = self.io_devices['interrupt_status'] & self.io_devices['interrupt_mask']
        
        if active_interrupts and self.io_callbacks['interrupt']:
            self.io_callbacks['interrupt'](active_interrupts)
    
    def register_io_callback(self, device, callback):
        """Register a callback function for I/O device events."""
        if device in self.io_callbacks:
            self.io_callbacks[device] = callback
        else:
            raise ValueError(f"Unknown I/O device: {device}")
    
    def add_console_input(self, char):
        """Add a character to the console input buffer."""
        if isinstance(char, str) and len(char) == 1:
            self.io_devices['console_in_buffer'].append(ord(char))
        elif isinstance(char, int) and 0 <= char <= 255:
            self.io_devices['console_in_buffer'].append(char)
        else:
            raise ValueError("Console input must be a single character or byte value")
        
        # Set interrupt if enabled
        self.io_devices['interrupt_status'] |= 0x1  # Bit 0 for console input
        self._check_interrupts()
    
    def add_keyboard_input(self, key_code):
        """Add a key code to the keyboard buffer."""
        self.io_devices['keyboard_buffer'].append(key_code)
        
        # Set interrupt if enabled
        self.io_devices['interrupt_status'] |= 0x2  # Bit 1 for keyboard
        self._check_interrupts()
    
    def update_timer(self, delta_ms):
        """Update the timer by the specified number of milliseconds."""
        if self.io_devices['timer_enabled']:
            self.io_devices['timer_value'] += delta_ms
            
            # Set interrupt if enabled
            self.io_devices['interrupt_status'] |= 0x4  # Bit 2 for timer
            self._check_interrupts()
    
    def clear_interrupt(self, interrupt_bit):
        """Clear a specific interrupt bit."""
        self.io_devices['interrupt_status'] &= ~interrupt_bit
    
    def load_program(self, instructions, start_address=0):
        """Load program instructions into memory."""
        address = start_address
        for instr in instructions:
            self.write_word(address, instr)
            address += 4
    
    def dump_memory(self, start_address, length):
        """Dump a section of memory for debugging."""
        end_address = start_address + length
        
        print(f"Memory dump from {hex(start_address)} to {hex(end_address-1)}:")
        print("Address    | Value (hex) | Value (dec) | ASCII")
        print("-" * 50)
        
        for addr in range(start_address, end_address, 4):
            if 0 <= addr < self.size - 3:
                value = self.read_word(addr)
                
                # Try to interpret as ASCII
                ascii_repr = ""
                for i in range(4):
                    byte_val = (value >> (i * 8)) & 0xFF
                    if 32 <= byte_val <= 126:  # Printable ASCII
                        ascii_repr += chr(byte_val)
                    else:
                        ascii_repr += "."
                
                print(f"0x{addr:08X} | 0x{value:08X} | {value:10} | {ascii_repr}")
            else:
                print(f"0x{addr:08X} | Out of bounds")