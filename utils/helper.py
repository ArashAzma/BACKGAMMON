def create_message(protocol, message):
    return f"{protocol}:{message}".encode()

def parse_message(data):
    decoded_data = data.decode()
    protocol, message = decoded_data.split(":", 1)
    return protocol, message