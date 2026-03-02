"""Module containing the parser for Anthem commands."""


class ParsedMessage:
    """Parsed message information."""

    command: str
    value: str
    input_number: int


def parse_message(message: str) -> ParsedMessage | None:
    """Parse a message to a ParsedMessage object."""
    if not message:
        return None
    return parse_x40_message(message)


def parse_x40_message(message: str) -> ParsedMessage | None:
    """Parse a message for x40 models."""
    if not message:
        return None
    return parse_x40_input_message(message, "ARC")


def parse_x40_input_message(message: str, command: str) -> ParsedMessage | None:
    """Parse a message for a specific input on x40 models."""
    if not message or not command:
        return None

    if message.startswith("IS") and command in message and len(message) >= len(command) + 4:
        try:
            parsed_message = ParsedMessage()
            command_position = message.index(command)
            parsed_message.command = message[: command_position + len(command)]

            input_number_str = message[2:command_position]
            if not input_number_str:
                return None

            parsed_message.input_number = int(input_number_str)
            if parsed_message.input_number < 1 or parsed_message.input_number > 99:
                return None

            parsed_message.value = message[command_position + len(command) :]
            return parsed_message
        except (ValueError, IndexError, UnicodeError):
            return None
    return None


def get_x40_input_command(input_number: int, command: str) -> str | None:
    """Return a formatted message for a specific input."""
    return f"IS{input_number}{command}" if input_number > 0 else None
