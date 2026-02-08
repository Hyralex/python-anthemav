"""Module containing the parser for Anthem command."""


class ParsedMessage:
    """Class containing parsed message information."""

    command: str
    value: str
    input_number: int


def parse_message(message: str) -> ParsedMessage | None:
    """Try to parse a message to a ParsedMessage object.
    
    Handles special characters and encoding issues gracefully by
    returning None for unparseable messages.
    """
    if not message:
        return None
    return parse_x40_message(message)


def parse_x40_message(message: str) -> ParsedMessage | None:
    """Try to parse a message for the x40 models.
    
    Handles special characters and encoding issues gracefully.
    """
    if not message:
        return None
    return parse_x40_input_message(message, "ARC")


def parse_x40_input_message(message: str, command: str) -> ParsedMessage | None:
    """Try to parse a message associated to a specific input for the x40 models.
    
    Handles special characters and encoding issues gracefully by validating
    input and returning None for invalid messages.
    """
    # Validate message format
    if not message or not command:
        return None
    
    if (
        message.startswith("IS")
        and command in message
        and len(message) >= len(command) + 4
    ):
        try:
            parsed_message = ParsedMessage()
            command_position = message.index(command)
            parsed_message.command = message[0 : command_position + len(command)]
            
            # Parse and validate input_number
            input_number_str = message[2:command_position]
            if not input_number_str:
                return None
            
            parsed_message.input_number = int(input_number_str)
            
            # Validate input_number range (1-99)
            if parsed_message.input_number < 1 or parsed_message.input_number > 99:
                return None
            
            # Extract value - handles special characters in the value string
            parsed_message.value = message[command_position + len(command) :]
            return parsed_message
        except (ValueError, IndexError, UnicodeError):
            # Handle parsing errors and encoding issues gracefully
            return None
    return None


def get_x40_input_command(input_number: int, command: str) -> str | None:
    """Return a formatted message for a specific input."""
    if input_number > 0:
        return f"IS{input_number}{command}"
    return None
