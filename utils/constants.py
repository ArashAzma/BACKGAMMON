import socket
from enum import Enum

SERVER = socket.gethostbyname(socket.gethostname())
SERVER_PORT = 5053
TO_CLIENT_PORT = 5555
BUFFER_SIZE = 2048
ONION_PORT = 6001
ONION_PORT_OPPONENT = 6004
BUFFER_SIZE = 1024


class MessageType(Enum):
    CONNECT = "connect"
    REQUEST = "request"
    ACCEPT = "accept"
    DECLINE = "decline"