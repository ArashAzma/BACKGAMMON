import socket
import threading
import ast
import sys
import pickle
from utils.key import *  
from utils.constants import * 

clients = []

def relay_node(server_address, relay_address, next_address, is_end_node, index, buffer_size=BUFFER_SIZE):
    relay_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    relay_socket.bind(relay_address)

    upstream_address = None
    upstream_count = 0

    while True:
        try:
            data, addr = relay_socket.recvfrom(buffer_size)
            
            if(addr == upstream_address or upstream_address is None):
                decrypted_message = decrypt_message(RELAY_KEYS[index], data)
                print(f'\t{addr} -> {relay_address}\tMessage: {decrypted_message.hex()[:20]}')

                if is_end_node:
                    relay_socket.sendto(decrypted_message, server_address)
                else:
                    relay_socket.sendto(decrypted_message, next_address)
                
                upstream_address = addr
            else:  
                encrypted_response = encrypt_message(RELAY_KEYS[index], data)
                relay_socket.sendto(encrypted_response, upstream_address)
                upstream_count+=1
                if(upstream_count==2):
                    upstream_count=0
                    upstream_address = None

        except Exception as e:
            print(f"Relay error: {e}")
            break
        
def relay_node_to_client(client_address, relay_address, next_address, is_end_node, index, buffer_size=BUFFER_SIZE):
    relay_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    relay_socket.bind(relay_address)

    upstream_address = None

    while True:
        try:
            data, addr = relay_socket.recvfrom(buffer_size)
            encrypted_response = encrypt_message(RELAY_KEYS[len(RELAY_KEYS) - index - 1], data)
            if is_end_node:
                relay_socket.sendto(encrypted_response, client_address)
            else:
                relay_socket.sendto(encrypted_response, next_address)
            upstream_address = addr
            
            data, _ = relay_socket.recvfrom(buffer_size)
            decrypted_message = decrypt_message(RELAY_KEYS[len(RELAY_KEYS) - index - 1], data)
            relay_socket.sendto(decrypted_message, upstream_address)
            break

        except Exception as e:
            print(f"Relay error: {e}")
            break
    relay_socket.close()

def setup_onion_routing(relay_ports, address, relay_function=relay_node):
    relay_addresses = [(SERVER, port) for port in relay_ports]
    
    for i in range(len(relay_addresses)):
        next_address = relay_addresses[i+1] if i < len(relay_addresses)-1 else None
        is_end_node = i == len(relay_addresses) - 1
        
        threading.Thread(
            target=relay_function, 
            args=(address, relay_addresses[i], next_address, is_end_node, i)
        ).start()
    
    return relay_addresses

def match_opponent(client1, client2):
    port = 5555
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind((SERVER, port))
    
    setup_onion_routing([ONION_PORT_OPPONENT, ONION_PORT_OPPONENT+1, ONION_PORT_OPPONENT+2], address=(SERVER, int(client2[1])), relay_function=relay_node_to_client)
    server.sendto(f"request:do you wanna play with {client1[1]}".encode(), (SERVER, ONION_PORT_OPPONENT))
    client_ans, address = server.recvfrom(BUFFER_SIZE)
    client_ans = client_ans.decode('utf-8')
    if client_ans == "accept" :
        server.sendto(f"ans:accepted".encode(), (SERVER, ONION_PORT+2))       
        try :
            clients.remove(client1)
            clients.remove(client2)
            server.sendto(f"0".encode('utf-8'), (SERVER, ONION_PORT+2))       
        except Exception as e:
            print(f"clients deleting error: {e}")
    else : 
        server.sendto("ans:notAccepted".encode(), (SERVER, ONION_PORT+2))       
        server.sendto(f"0".encode('utf-8'), (SERVER, ONION_PORT+2))       


def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind((SERVER, SERVER_PORT))
    print(f"Server listening on ({SERVER}, {SERVER_PORT})")
    setup_onion_routing([ONION_PORT, ONION_PORT+1, ONION_PORT+2], address=(SERVER, SERVER_PORT))
    
    while(True):
        while True:
            data, address = server.recvfrom(BUFFER_SIZE)
            data = data.decode('utf-8')
            message, message_type = data.split(':')[:-1], data.split(':')[-1]
            
            match message_type:
                case MessageType.CONNECT.value:
                    client_address = message[0]
                    print(f"\n------Connection from {address} Message: {client_address}------\n")
                    client_address = ast.literal_eval(client_address)

                    if(client_address not in clients):
                        clients.append(client_address) 
                        server.sendto('ready'.encode('utf-8'), address)
                        serialized_clients = pickle.dumps(clients)
                        server.sendto(serialized_clients, address)
                        
                case MessageType.REQUEST.value:
                    print(f"\n------Request from {address} Message: {message}------\n")
                    client1, client2 = message
    
                    client1 = (SERVER, int(client1))
                    client2 = (SERVER, int(client2))
                    match_opponent(client1, client2)
                case _:
                    pass
            
start_server()
sys.exit(0)