import socket
import threading
import pickle
import os
from utils.key2 import *
from utils.constants import *
from utils.helper import *
import rsa
from base64 import b64encode, b64decode

clients = []

'''
Public  Keys: encrypt
Private Keys: decrypt

AT FIRST I SHOULD SEND A MESSAGE TO START_RELAY TO GIVE HIM ITS PRIVATE KEY AND GET AN ACK 

THEN ENCRYPT USING THE PUBLIC KEY AND SEND THE KEY TO THE MIDDLE NODE
DO THIS UNTIL ALL 3 ARE DONE
'''

def relay_node(relay_address, next_address, index, buffer_size=BUFFER_SIZE):
    relay_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    relay_socket.bind(relay_address)
    relay_socket.listen(5)

    # print(f"Relay node {index} started at {relay_address} forwarding to {next_address}")

    CONNECTION_MODE = True
    
    private_key = None
    times = 0
    next_node_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    next_node_socket.connect(next_address)    
    client_conn, client_addr = relay_socket.accept()
    
    while True:
        try:
            if(CONNECTION_MODE):
                if private_key is None:
                    data = client_conn.recv(buffer_size)
                    if (len(data) == 0):
                        continue
                    private_key = load_private_key(data.decode())
                    message = create_message(MessageType.CONNECT.value, 'success')
                    client_conn.send(message)

                else:
                    times+=1
                    num_chunks = int(client_conn.recv(buffer_size).decode())
                    encrypted_chunks = []
                    for _ in range(num_chunks):
                        chunk_size = int.from_bytes(client_conn.recv(4), byteorder='big')
                        chunk = client_conn.recv(chunk_size)
                        encrypted_chunks.append(chunk)
                    
                    if index==0 and times==2:
                        intermediate_chunks = []
                        for chunk in encrypted_chunks:
                            try:
                                decrypted_bytes = decrypt2(chunk, private_key)  
                                decrypted_bytes = remove_padding(decrypted_bytes)
                                intermediate_chunks.append(decrypted_bytes)
                            except Exception as e:
                                print(f"Decryption error: {e}")
                                
                        ccc = []
                        i = 0
                        while (i+1 < len(intermediate_chunks)):
                            ccc.append(intermediate_chunks[i] + intermediate_chunks[i+1])
                            i+=2
                        
                        next_node_socket.sendall(str(len(ccc)).encode())
                        for chunk in ccc:
                            chunk_size = len(chunk).to_bytes(4, byteorder='big')
                            next_node_socket.sendall(chunk_size + chunk)

                    elif index==1 and times==1:
                        d = decrypt_and_reassemble_key(encrypted_chunks, private_key)
                        next_node_socket.sendall(d)

                    else:
                        private_key_bytes = decrypt_and_reassemble_key(encrypted_chunks, private_key)
                        next_node_socket.sendall(private_key_bytes)                       
                        
                    data = next_node_socket.recv(BUFFER_SIZE)
                    client_conn.sendall(data)
                    
                if (index==0 and times == 2):
                    CONNECTION_MODE = False
                if (index==1 and times == 1):
                    CONNECTION_MODE = False
                if (index==2 and times == 0):
                    CONNECTION_MODE = False
            else:
                print(f'{index} Listening')
                data = client_conn.recv(buffer_size)
                data = decrypt_message(data, private_key)
                next_node_socket.sendall(data)
                if index == 2:
                    print('FINAL MESSAGE', data.decode())
                else:
                    next_node_socket.sendall(data)
                break


        except Exception as e:
            print(f"Relay error at node {index}: {e}")
            break

def setup_onion_routing(relay_ports, address, relay_function=relay_node):
    relay_addresses = [(SERVER, port) for port in relay_ports]

    for i in range(len(relay_addresses)):
        next_address = relay_addresses[i + 1] if i < len(relay_addresses) - 1 else address

        threading.Thread(
            target=relay_function,
            args=(relay_addresses[i], next_address, i),
            daemon=True
        ).start()

    return relay_addresses

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((SERVER, SERVER_PORT))
    server.listen(10)
    print(f"Server started on {SERVER}:{SERVER_PORT}")

    for i in range(4):
        p = i * 3
        setup_onion_routing(
            relay_ports=[ONION_PORT + p, ONION_PORT + p + 1, ONION_PORT + p + 2],
            address=(SERVER, SERVER_PORT)
        )

    while True:
        conn, addr = server.accept()
        data = conn.recv(BUFFER_SIZE)
        if not data:
            continue

        print(f"Server received connection from {addr}")
        address, message = parse_message(data)
        print(f"Received: {message}")

        if message == MessageType.CONNECT.value:
            if(address not in clients):
                serialized_clients = pickle.dumps(clients)
                message = create_message(MessageType.ACCEPT.value, serialized_clients.hex())
                conn.sendall(message)
                clients.append(address)
                print(clients)
        elif message == MessageType.ONLINES.value :
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect(address)
            client_socket.send(clients)
            print("i got onlines!")

        conn.close()


if os.path.isfile(CLIENTS_FILE):
    os.remove(CLIENTS_FILE)
    
with open(CLIENTS_FILE, "a") as f:
    f.write("0")
        
start_server()