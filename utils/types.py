from enum import Enum

class MessageType(Enum):
    CONNECT = "connect"
    REQUEST = "request"
    ACCEPT = "accept"
    DECLINE = "decline"