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

    print(f"Relay node {index} started at {relay_address} forwarding to {next_address}")

    CONNECTION_MODE = True
    
    private_key = None

    next_node_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    next_node_socket.connect(next_address)    
    client_conn, client_addr = relay_socket.accept()
    
    while True:
        # print(f'{index} connected {client_addr}')
        try:
            if(CONNECTION_MODE):
                
                if private_key is None:
                    data = client_conn.recv(buffer_size)
                    if (len(data) == 0):
                        continue
                    print(f'{index} recv {data} {len(data)}')
                    _, private_key = parse_message(data)
                    print(f'{index} success', private_key)
                    message = create_message(MessageType.CONNECT.value, 'success')
                    client_conn.send(message)
                else:
                    print(f'{index} is DONE')
                    data = client_conn.recv(buffer_size)
                    print('got encrypted_data')
                    print(private_key)
                    decrypted_data = decrypt(data, private_key)
                    print('got decrypted_data')
                    print("Received message:", decrypted_data.decode())
                    print('Data received successfully')
                
                
                # client_conn, client_addr = relay_socket.accept()
                # print(f"Relay node {index} connected to {client_addr}")

                # next_node_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                # next_node_socket.connect(next_address)

                # data = client_conn.recv(buffer_size)
                # if not data:
                #     break 
                
                # decrypted_message = data.decode()
                # # print(f"\t{client_addr} -> {relay_address}\tMessage: {decrypted_message}")

                # next_node_socket.sendall(data)

                # response = next_node_socket.recv(buffer_size)
                # if response:
                #     # print(f"\t{next_address} -> {relay_address}\tResponse received")
                #     client_conn.sendall(response)

                # next_node_socket.close()
                # client_conn.close()

        except Exception as e:
            print(f"Relay error at node {index}: {e}")

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

    for i in range(1):
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
        protocol, message = parse_message(data)

        if protocol == MessageType.CONNECT.value:
            print(f"Received: {message}")
            client_address = message
            if(client_address not in clients):
                serialized_clients = pickle.dumps(clients)
                message = create_message(MessageType.ACCEPT.value, serialized_clients.hex())
                conn.sendall(message)
                clients.append(client_address)
                

        conn.close()


if os.path.isfile(CLIENTS_FILE):
    os.remove(CLIENTS_FILE)
    
with open(CLIENTS_FILE, "a") as f:
    f.write("0")
        
start_server()