import socket
from enum import Enum

SERVER = socket.gethostbyname(socket.gethostname())
SERVER_PORT = 5053
TO_CLIENT_PORT = 5555
BUFFER_SIZE = 2048
ONION_PORT = 6001
ONION_PORT_OPPONENT = 6004
BUFFER_SIZE = 8192
CLIENTS_FILE = 'clients.txt'

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BROWN = (139, 69, 19)
BEIGE = (245, 222, 179)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GRAY = (128, 128, 128)

WINDOW_SIZE = 806
BOARD_SIZE = 600
CHAT_HEIGHT = 200
PIECE_RADIUS = 20
FONT_SIZE = 15
class MessageType(Enum):
    CONNECT = "connect"
    REQUEST = "r"
    ACCEPT = "a"
    DECLINE = "decline"
    TOSERVER = "toServer"
    TOCLIENT = "toClient"
    ONLINES = "onlines"
    ANYREQUEST = "anyrequest"
    REQUESTS = "requests"
    ANYACCEPT = "anyAccept"
    ANYACCEPTRES = "anyAcceptres"