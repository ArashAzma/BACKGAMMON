import socket
import pickle
import time
import base64
from utils.key2 import * 
from utils.constants import * 
from utils.helper import * 
import rsa
from base64 import b64encode, b64decode
import zlib



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
    
    for i in range(3):
        node_private, node_public = generate_keys()
        private_keys.append(node_private)
        public_keys.append(node_public)
        
    return private_keys, public_keys

def decrypt_server_message(message, private_keys):
    for pk in private_keys:
        message = decrypt_message(message, pk)
        
    return message
    
def connect_to_server():
    CONNECTION_MODE = True
    port = find_my_port()
    
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((SERVER, port))
    my_address = client_socket.getsockname()
    print(f' MY ADDRESS {my_address} --- MY NODE PORT {port}')
    
    private_keys, public_keys = generate_client_keys()
        
    #! Send private key 0
    client_socket.sendall(serialize_private_key(private_keys[0]))
    # print('sent key 0')
    
    data = client_socket.recv(BUFFER_SIZE)
    protocol, message = parse_message(data)
    print('PRIVATE KEY 0 was a SUCCESS:', message)
    
    #! Send private key 1
    private_key_bytes = serialize_private_key(private_keys[1])
    encrypted_chunks = split_and_encrypt_key(private_key_bytes, 214, public_keys[0])
    client_socket.sendall(str(len(encrypted_chunks)).encode())
    for chunk in encrypted_chunks:
        chunk_size = len(chunk).to_bytes(4, byteorder='big')
        client_socket.sendall(chunk_size + chunk)
    # print('sent key 1')
    
    data = client_socket.recv(BUFFER_SIZE)
    protocol, message = parse_message(data)
    print('PRIVATE KEY 1 was a SUCCESS:', message)
        
    #! Send private key 2
    
    final_chunks = []
    private_key_bytes = serialize_private_key(private_keys[2])
    encrypted_chunks = split_and_encrypt_key(private_key_bytes, 190, public_keys[1])
    for chunk in encrypted_chunks:
        encrypted_chunks = split_and_encrypt_key(chunk, 190, public_keys[0])
        for ch in encrypted_chunks:
            final_chunks.append(ch)
        
    client_socket.sendall(str(len(final_chunks)).encode())
    for chunk in final_chunks:
        chunk_size = len(chunk).to_bytes(4, byteorder='big')
        client_socket.sendall(chunk_size + chunk)
    # print('sent key 2')

    data = client_socket.recv(BUFFER_SIZE)
    protocol, message = parse_message(data)
    print('PRIVATE KEY 2 was a SUCCESS:', message)
    
    #! Send public keys
    for i, pk in enumerate(public_keys):
        client_socket.sendall(serialize_public_key(pk))
        # print(f'sent public key {i}')
        data = client_socket.recv(BUFFER_SIZE)
        protocol, message = parse_message(data)
        print(f'PUBLIC KEY {i} was a SUCCESS:', message)
    
    ########################################################
    ########################################################
    
    
    message = create_message("connect", my_address)
    for key in reversed(public_keys):
        message = encrypt_message(message, key)
        # message = create_message(MessageType.TOSERVER.value, message)
        # message = create_message(MessageType.TOSERVER.value, message)

    client_socket.sendall(message)
    print('Sent connect')
    
    data = client_socket.recv(BUFFER_SIZE)
    data = decrypt_server_message(data, private_keys)
    protocol, data = parse_client_message(data)
    if protocol == MessageType.ACCEPT.value:
        clients = pickle.loads(data)
        print('Clients successfully connected to the Server')
        print('clients', clients)
    else:
        print('There was an Error with Clients')
    
    # client_socket.sendall((MessageType.TOSERVER.value+':').encode() + base64.b64encode(message))
    
    # message = create_message(MessageType.ONLINES.value, "Salam")
    # for key in reversed(public_keys):
    #     message = encrypt_message(message, key)
    # client_socket.sendall(message)
    # print('Sent onlines')
    
connect_to_server()