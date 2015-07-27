class ArgumentError(Exception):
    """Exception raised when a command has invalid arguments."""
    def __init__(self, arg=None, msg=None):
        self.arg = arg
        self.msg = msg

    def __str__(self):
        return self.arg + ' ' + self.msg
