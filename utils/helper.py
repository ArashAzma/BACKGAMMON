def create_message(protocol, message):
    return f"{protocol}:{message}".encode()

def parse_message(data):
    decoded_data = data.decode()
    protocol, message = decoded_data.split(":", 1)
    return protocol, message

def create_client_message(message_type: str, payload: bytes) -> bytes:
    """
    Create a message by concatenating type and payload with a separator.
    Avoids double encoding by keeping payload as raw bytes.
    """
    # Convert message type to bytes and combine with payload
    header = message_type.encode()
    # Use a separator that won't appear in the pickle data
    return header + b":" + payload

def parse_client_message(message: bytes) -> tuple[str, bytes]:
    """
    Parse a message into type and payload, keeping payload as raw bytes.
    """
    # Split on first occurrence of separator
    header, payload = message.split(b":", 1)
    return header.decode(), payload