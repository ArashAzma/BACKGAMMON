import socket
import threading
import pickle
import os
from utils.key2 import *
from utils.constants import *
from utils.helper import *
import time
import random
import json

clients = []
requests_list = []
declines = []
accepts = []

def roll_dice():
    roll1 = random.randint(1, 6)
    roll2 = random.randint(1, 6)
    current_roll = [roll1, roll2]
    if roll1 == roll2:
        current_roll *= 2
        
    return current_roll
    
def relay_node(relay_address, next_address, index, buffer_size=BUFFER_SIZE):
    relay_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    relay_socket.bind(relay_address)
    relay_socket.listen(5)

    # print(f"Relay node {index} started at {relay_address} forwarding to {next_address}")

    CONNECTION_MODE = True
    PUBLIC_MODE = False
    
    private_key = None
    public_key = None
    times = 0
    next_node_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    next_node_socket.connect(next_address)    
    pre_node_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)    
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
                    times = 0
                    CONNECTION_MODE = False
                    PUBLIC_MODE = True
                if (index==1 and times == 1):
                    times = 0
                    CONNECTION_MODE = False
                    PUBLIC_MODE = True
                if (index==2 and times == 0):
                    times = 0
                    CONNECTION_MODE = False
                    PUBLIC_MODE = True
                    
            elif PUBLIC_MODE:
                data = client_conn.recv(BUFFER_SIZE)
                
                if public_key is None:
                    public_key = load_public_key(data.decode())
                    message = create_message(MessageType.CONNECT.value, 'success')
                    client_conn.send(message)
                    # print(f' {index} public_key {public_key}')
                else:
                    times+=1
                    next_node_socket.sendall(data)
                    data = next_node_socket.recv(BUFFER_SIZE)
                    client_conn.sendall(data)
                
                if (index==0 and times == 2):
                    PUBLIC_MODE = False
                if (index==1 and times == 1):
                    PUBLIC_MODE = False
                if (index==2 and times == 0):
                    PUBLIC_MODE = False    
                
            else:
                    next_node_socket.setblocking(False)
                    client_conn.setblocking(False)
                    while(True):
                        try :
                            data = next_node_socket.recv(buffer_size)
                            if data != b'' :       
                                data = encrypt_message(data, public_key)
                                client_conn.sendall(data)
                                data = b''
                        except BlockingIOError:
                            pass
                        try :
                            data = client_conn.recv(buffer_size)
                            if data != b'' :       
                                data = decrypt_message(data, private_key)    
                                next_node_socket.sendall(data)
                                data = b''
                        except BlockingIOError:
                            pass                            
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

def handle_client(conn, addr):
    global requests_list, declines, accepts
    print(f"New connection from {addr}")
    try:
        while True:
    
            data = conn.recv(BUFFER_SIZE)
            if not data:
                break
            
            protocol, message = parse_message(data)
            if protocol == MessageType.CONNECT.value:
                address = message
                if(address not in clients):
                    serialized_clients = pickle.dumps(clients)
                    message = create_message(MessageType.ACCEPT.value, serialized_clients.hex())
                    clients.append(address)
            elif protocol == MessageType.ANYREQUEST.value:
                # client_address, opponent_address = message.split(b";", 1)
                
                serialized_requests = pickle.dumps([entry for entry in requests_list if entry.split(";")[1] == message])
                serialized_clients = pickle.dumps(clients)

                response = create_client_message(MessageType.ONLINES.value, serialized_clients)
                conn.sendall(response)

                time.sleep(0.1)

                response = create_client_message(MessageType.REQUESTS.value, serialized_requests)
                conn.sendall(response)

            elif protocol == MessageType.REQUEST.value:
                requests_list.append(message)
            elif protocol == MessageType.ACCEPT.value:
                accepts.append(message)
                for entry in requests_list :
                    if (entry.split(";")[0] == message.split(";")[1] and entry.split(";")[1] == message.split(";")[0]):
                        requests_list.remove(entry)
            elif protocol == MessageType.DECLINE.value:
                declines.append(message)    
                for entry in requests_list :
                    if (entry.split(";")[0] == message.split(";")[1] and entry.split(";")[1] == message.split(";")[0]):
                        requests_list.remove(entry)
            elif protocol == MessageType.ANYACCEPT.value:
                serialized_accepts = pickle.dumps([entry.split(";")[0] for entry in accepts if entry.split(";")[1] == message])
                serialized_declines = pickle.dumps([entry.split(";")[0] for entry in declines if entry.split(";")[1] == message])
                
                response = create_client_message(MessageType.ANYACCEPTRES.value, serialized_accepts)
                conn.sendall(response)

                time.sleep(0.1)

                response = create_client_message(MessageType.ANYACCEPTRES.value, serialized_declines)
                conn.sendall(response)           
                try :    
                    for entry in declines :
                        if (entry.split(";")[1] == message):
                            declines.remove(entry)
                except Exception :
                    pass

                try :    
                    for entry in accepts :
                        if (entry.split(";")[1] == message):
                            accepts.remove(entry)
                except Exception :
                    pass
            elif protocol == MessageType.ROLL_DICE.value:
                rolls = roll_dice()
                serialized_rolls = pickle.dumps(rolls)
                response = create_client_message(MessageType.ROLL_DICE.value, serialized_rolls)
                conn.sendall(response)
            elif protocol == MessageType.FINISHED_GAME.value:
                message = eval(message)
                if message['xFree']== 15:
                    response = create_client_message(MessageType.ROLL_DICE.value, "xWins".encode())
                elif message['oFree'] == 15:
                    response = create_client_message(MessageType.ROLL_DICE.value, "oWins".encode())
                else:
                    response = create_client_message(MessageType.ROLL_DICE.value, "continue".encode())
                    
                conn.sendall(response)
                
            elif protocol == MessageType.TESTING.value:
                conn.sendall("i can talk to you".encode())

    except Exception as e:
        print(f"Error handling client: {e}")
    finally:
        conn.close()


def start_server():
    global requests_list
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((SERVER, SERVER_PORT))
    server.listen(100)
    print(f"Server started on {SERVER}:{SERVER_PORT}")

    for i in range(4):
        p = i * 3
        setup_onion_routing(
            relay_ports=[ONION_PORT + p, ONION_PORT + p + 1, ONION_PORT + p + 2],
            address=(SERVER, SERVER_PORT)
        )

    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

if os.path.isfile(CLIENTS_FILE):
    os.remove(CLIENTS_FILE)
    
with open(CLIENTS_FILE, "a") as f:
    f.write("0")
        
start_server()