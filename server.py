import socket
import threading
import ast
import time
import sys
from utils.key import *  

SERVER = socket.gethostbyname(socket.gethostname())
SERVER_PORT = 5053
BUFFER_SIZE = 2048

def relay_node(server_address, relay_address, next_address, is_end_node, index, buffer_size=1024):
    relay_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    relay_socket.bind(relay_address)
    
    print(f"{index} Relay Node {relay_address} initialized")
    upstream_address = None
    
    while True:
        try:
            data, addr = relay_socket.recvfrom(buffer_size)
            decrypted_message = decrypt_message(RELAY_KEYS[index], data)
            print(f'\t{addr} -> {relay_address}\tMessage: {decrypted_message.hex()[:20]}')
            
            if is_end_node:
                relay_socket.sendto(decrypted_message, server_address)
            else:
                relay_socket.sendto(decrypted_message, next_address)
                   
            upstream_address = addr
            response, server_addr = relay_socket.recvfrom(buffer_size)
            encrypted_response = encrypt_message(RELAY_KEYS[index], response)
            relay_socket.sendto(encrypted_response, upstream_address)
            # print(f'\t{relay_address} -> {upstream_address}')
        except Exception as e:
            print(f"Relay error: {e}")
            break

def setup_onion_routing(host):
    relay_ports = [6001, 6002, 6003]
    relay_addresses = [(SERVER, port) for port in relay_ports]
    server_address  = (SERVER, host)
    
    for i in range(len(relay_addresses)):
        next_address = relay_addresses[i+1] if i < len(relay_addresses)-1 else None
        is_end_node = i == len(relay_addresses) - 1
        
        threading.Thread(
            target=relay_node, 
            args=(server_address, relay_addresses[i], next_address, is_end_node, i)
        ).start()
    
    return relay_addresses

def setup_onion_routing_toClient(host):
    relay_ports = [6004, 6005, 6006]
    relay_addresses = [(SERVER, port) for port in (relay_ports)]
    server_address  = (SERVER, host)
    
    for i in range(len(relay_addresses)):
        next_address = relay_addresses[i+1] if i < len(relay_addresses)-1 else None
        is_end_node = i == len(relay_addresses) - 1
        
        threading.Thread(
            target=relay_node, 
            args=(server_address, relay_addresses[i], next_address, is_end_node, i)
        ).start()
    
    return relay_addresses


def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind((SERVER, SERVER_PORT))
    print(f"Server listening on ({SERVER}, {SERVER_PORT})")
    setup_onion_routing(SERVER_PORT)
    
    clients = []
    while(True):
        while len(clients) < 2:
            data, address = server.recvfrom(BUFFER_SIZE)
            data = data.decode('utf-8')
            truth_bit, client_address = data.split(':')[-2:]
            
            print(f"\n**Connection from {address} Message: {client_address}\n")
            
            if(truth_bit != '0'):
                continue

            client_address = ast.literal_eval(client_address)

            if(client_address not in clients):
                clients.append(client_address) 
                server.sendto('ready'.encode('utf-8'), address)
        
        client1, client2 = clients
        clients.pop()
        clients.pop()
        time.sleep(.1)
        # setup_onion_routing_toClient(client2)
        # server.sendto(f"{client1[0]} {client1[1]} {SERVER_PORT}".encode(), (SERVER, 6004))
        # setup_onion_routing_toClient(client1)
        # server.sendto(f"{client2[0]} {client2[1]} {SERVER_PORT}".encode(), 6003)
        server.sendto(f"{client1[0]} {client1[1]} {SERVER_PORT}".encode(), client2)
        server.sendto(f"{client2[0]} {client2[1]} {SERVER_PORT}".encode(), client1)
    
start_server()
sys.exit(0)