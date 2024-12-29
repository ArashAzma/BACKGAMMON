import socket
import pickle
import time
from utils.key2 import * 
from utils.constants import * 
from utils.helper import * 

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((SERVER, ONION_PORT))
my_address = client_socket.getsockname()

def connect_to_server():
    message = create_message(MessageType.CONNECT.value, my_address)
    
    client_socket.sendall(message)
    data = client_socket.recv(BUFFER_SIZE)
    
    protocol, message = parse_message(data)
    if protocol == MessageType.ACCEPT.value:
        clients_bytes = bytes.fromhex(message)
        clients = pickle.loads(clients_bytes)

        print(f"SERVER ACCEPTED: {clients}")
    
    
print(f'MY ADDRESS ========> {my_address}')
connect_to_server()