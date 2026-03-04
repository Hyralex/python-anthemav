class DeviceError(Exception):
    """Error triggered when the device couldn't initialised by receiving the basic information"""

    def __init__(self, message: str = "Device initialization failed", context: dict | None = None):
        """Initialize DeviceError with message and optional context.

        Args:
            message: Error message describing the failure
            context: Optional dictionary with additional error context
        """
        self.message = message
        self.context = context or {}
        super().__init__(self.message)
