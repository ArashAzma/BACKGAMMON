import socket
from enum import Enum

SERVER = socket.gethostbyname(socket.gethostname())
SERVER_PORT = 5053
TO_CLIENT_PORT = 5555
BUFFER_SIZE = 2048
ONION_PORT = 6001
ONION_PORT_OPPONENT = 6004
BUFFER_SIZE = 1024

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
FONT_SIZE = 20
WINDOW_SIZE = 600
class MessageType(Enum):
    CONNECT = "connect"
    REQUEST = "request"
    ACCEPT = "accept"
    DECLINE = "decline"