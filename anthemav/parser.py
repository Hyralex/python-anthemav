"""Module containing the parser for Anthem command."""


class ParsedMessage:
    """Class containing parsed message information."""

    command: str
    value: str
    input_number: int
    zone: int


def parse_message(message: str) -> ParsedMessage | None:
    """Try to parse a message to a ParsedMessage object.
    
    Dispatcher that tries all known formats (x40, x20/MDX) automatically.
    This is used as a fallback when no model is available.
    
    For model-specific parsing, use model.parse_message() instead.
    
    Handles special characters and encoding issues gracefully by
    returning None for unparseable messages.
    """
    if not message:
        return None
    
    # Try x40 format first (ISxCOMMAND format)
    result = parse_x40_message(message)
    if result:
        return result
    
    # Try x20/MDX format (ISNxx format)
    result = parse_x20_message(message)
    if result:
        return result
    
    return None


def parse_x40_message(message: str) -> ParsedMessage | None:
    """Try to parse a message for the x40 models.
    
    Handles both ARC and IN command formats.
    Handles special characters and encoding issues gracefully.
    """
    if not message:
        return None
    
    # Try ARC command
    result = parse_x40_input_message(message, "ARC")
    if result:
        return result
    
    # Try IN command (input names)
    result = parse_x40_input_message(message, "IN")
    if result:
        return result
    
    return None


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
            parsed_message.zone = 0  # x40 format doesn't encode zone in message
            return parsed_message
        except (ValueError, IndexError, UnicodeError):
            # Handle parsing errors and encoding issues gracefully
            return None
    return None


def parse_x20_message(message: str) -> ParsedMessage | None:
    """Try to parse a message for the x20/MDX models.
    
    Handles ISNxx format where xx is a two-digit input number.
    Handles special characters and encoding issues gracefully.
    """
    if not message or not message.startswith("ISN") or len(message) < 5:
        return None
    
    try:
        parsed_message = ParsedMessage()
        parsed_message.command = "ISN"
        
        # Parse input number from positions 3-5 (ISNxx)
        parsed_message.input_number = int(message[3:5])
        
        # Validate input_number range (1-99)
        if parsed_message.input_number < 1 or parsed_message.input_number > 99:
            return None
        
        # Extract value - everything after ISNxx
        parsed_message.value = message[5:]
        parsed_message.zone = 0  # x20/MDX format doesn't encode zone in message
        return parsed_message
    except (ValueError, IndexError):
        # Handle parsing errors gracefully
        return None


def get_x40_input_command(input_number: int, command: str) -> str | None:
    """Return a formatted message for a specific input."""
    if input_number > 0:
        return f"IS{input_number}{command}"
    return None


def format_message(parsed: ParsedMessage, model_series: str) -> str:
    """Format a parsed message back to string (pretty printer).
    
    This is a convenience function for backward compatibility.
    For model-specific formatting, use model.format_message() instead.
    
    Args:
        parsed: ParsedMessage object to format
        model_series: Model series identifier ('x20', 'x40', 'mdx')
    
    Returns:
        Formatted message string, or empty string if format not supported
    """
    if not parsed or not model_series:
        return ""
    
    if model_series == "x40":
        # x40 format: ISxCOMMAND where COMMAND is ARC or IN
        if parsed.command.endswith("ARC"):
            return f"IS{parsed.input_number}ARC{parsed.value}"
        elif parsed.command.endswith("IN"):
            return f"IS{parsed.input_number}IN{parsed.value}"
    elif model_series in ["x20", "mdx"]:
        # x20/MDX format: ISNxx
        if parsed.command == "ISN":
            return f"ISN{parsed.input_number:02d}{parsed.value}"
    
    return ""
