import socket
import pickle
import time
from utils.key2 import * 
from utils.constants import * 
from utils.helper import * 
import rsa
from base64 import b64encode, b64decode


def find_my_port():
    my_start_node = ONION_PORT
    with open(CLIENTS_FILE, "r+") as f:
        number_of_clients = f.read().strip()
        number_of_clients = int(number_of_clients)
        my_start_node += 3 * number_of_clients
        number_of_clients += 1 
        f.seek(0)
        f.write(str(number_of_clients))
        f.truncate()
        
    return my_start_node
    
def generate_client_keys():
    private_keys = []
    public_keys = []
    
    for prime in [23, 29, 31]:
        node_public, node_private = generate_keys(prime)
        private_keys.append(node_private)
        public_keys.append(node_public)
        
    return private_keys, public_keys
    
def connect_to_server():
    CONNECTION_MODE = True
    port = find_my_port()
    
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((SERVER, port))
    my_address = client_socket.getsockname()
    print(f' MY ADDRESS {my_address} --- MY NODE PORT {port}')
    
    private_keys, public_keys = generate_client_keys()
        
    # for i in range(3):
    message = create_message(MessageType.CONNECT.value, private_keys[0])
    client_socket.sendall(message)
    print('sent key 0')
    data = client_socket.recv(BUFFER_SIZE)
    protocol, message = parse_message(data)
    print('message:', message)
    
    enc_key = encrypt(private_keys[1], public_keys[0])
    message = create_message(MessageType.CONNECT.value, enc_key)
    client_socket.sendall(message)
    print('sent key 1')
    data = client_socket.recv(BUFFER_SIZE)
    protocol, message = parse_message(data)
    print('message:', message)
    
connect_to_server()