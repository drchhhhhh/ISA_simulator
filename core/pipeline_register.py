class PipelineRegister:
    """Represents a pipeline register between stages."""
    
    def __init__(self, name):
        self.name = name
        self.data = {}
    
    def write(self, key, value):
        """Write a value to the pipeline register."""
        self.data[key] = value
    
    def read(self, key):
        """Read a value from the pipeline register."""
        return self.data.get(key)
    
    def clear(self):
        """Clear all values in the pipeline register."""
        self.data = {}