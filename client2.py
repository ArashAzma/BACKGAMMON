import socket
import pickle
import time
from utils.key2 import * 
from utils.constants import * 
from utils.helper import * 
import rsa
from base64 import b64encode, b64decode
import zlib
import pygame
import threading
import random


def generate_client_keys():
    private_keys = []
    public_keys = []
    
    for i in range(3):
        node_private, node_public = generate_keys()
        private_keys.append(node_private)
        public_keys.append(node_public)
        
    return private_keys, public_keys

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

#-----------------------------------------------------------------
private_keys, public_keys = generate_client_keys()
port = find_my_port()
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((SERVER, port))
alone = True
my_address = client_socket.getsockname()
#------------------------------------------------------------------

def three_layerEncrypt(message) :
    global public_keys
    for key in reversed(public_keys):
        message = encrypt_message(message, key)
    return message

def show_online_users(clients):
    users = clients.copy()
    users.remove(my_address)
            
    if(len(users) > 0):
        print('\nOnline players:')
        for client in users:
            print('\t',client[1])
    else:
        print('Nobody is online')


def roll_dice():
    global current_roll, moves_left
    roll1 = random.randint(1, 6)
    roll2 = random.randint(1, 6)
    current_roll = [roll1, roll2]
    if roll1 == roll2:
        current_roll *= 2
    moves_left = sum(current_roll)

def handle_network_message(data):
    global board, is_my_turn
    try:
        message = pickle.loads(data)
        if isinstance(message, dict):
            if 'board' in message:
                board.myBoard = message['board']
                if message.get('turn_end', False):
                    is_my_turn = True
                    roll_dice()
        elif isinstance(message, str):
            if message.startswith('CHAT:'):
                messages.append(f"Opponent: {message[5:]}")
                
    except Exception as e:
        messages.append(f"Error: {str(e)}")


def listen_loop(buffer_size=BUFFER_SIZE):
    global messages
    while True:
        try:
            data, _ = client_socket.recvfrom(buffer_size)
            handle_network_message(data)
        except Exception as e:
            messages.append(f"Listen error: {e}")
            break

def decline():
    choose_opoonent_msg = create_message("decline", "ans")
    client_socket.sendto(choose_opoonent_msg, (SERVER, 6006))
    return

def accept() :
    global alone, opponent, requested
    choose_opoonent_msg = create_message("accept", "ans")
    client_socket.sendto(choose_opoonent_msg, (SERVER, 6006))
    opponent_port = requested
    opponent = (SERVER, int(opponent_port))
    alone = False
    return


def send_request() :
    global opponent_port, client_socket
    message = create_message(my_address, MessageType.ONLINES.value)
    message = three_layerEncrypt(message)
    client_socket.send(message)
    # clients = client_socket.recv(5*len(my_address))
    # print(clients)
    print("enter your opponent :")
    opponent_port = input()
    opponent_address = (SERVER, opponent_port)
    message = f"{my_address}:{opponent_address}"
    choose_opoonent_msg = create_message(message, MessageType.REQUEST)
    client_socket.send(choose_opoonent_msg)

def connect_to_server():
    global private_keys, public_keys, alone, my_address, client_socket
    CONNECTION_MODE = True
    print(f' MY ADDRESS {my_address} --- MY NODE PORT {port}')
    
    #! Send private key 0
    client_socket.sendall(serialize_private_key(private_keys[0]))
    print('sent key 0')
    
    data = client_socket.recv(BUFFER_SIZE)
    protocol, message = parse_message(data)
    print('KEY 0 was a SUCCESS:', message)
    
    #! Send private key 1
    private_key_bytes = serialize_private_key(private_keys[1])
    encrypted_chunks = split_and_encrypt_key(private_key_bytes, 214, public_keys[0])
    client_socket.sendall(str(len(encrypted_chunks)).encode())
    for chunk in encrypted_chunks:
        chunk_size = len(chunk).to_bytes(4, byteorder='big')
        client_socket.sendall(chunk_size + chunk)
    print('sent key 1')
    
    data = client_socket.recv(BUFFER_SIZE)
    protocol, message = parse_message(data)
    print('KEY 1 was a SUCCESS:', message)
        
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
    print('sent key 2')

    data = client_socket.recv(BUFFER_SIZE)
    protocol, message = parse_message(data)
    print('KEY 2 was a SUCCESS:', message)

    # connecting client
    message = create_message(my_address, MessageType.CONNECT.value)
    message = three_layerEncrypt(message)
    client_socket.sendall(message)    
    
    message = create_message(my_address, MessageType.ONLINES.value)
    message = three_layerEncrypt(message)
    client_socket.sendall(message)    
        
    # requesting
    while (alone) :
        word = input()
        print(word)
        match word :
            case MessageType.REQUEST.value :
                send_request()
            case MessageType.ACCEPT.value :
                accept()
            case MessageType.DECLINE.value : 
                decline()

    # pygame.init()
    # screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
    # font = pygame.font.Font(None, FONT_SIZE)
    # title = "BLACK"
    # if my_address[1] > opponent[1]:
    #     title = "WHITE"
        
    # pygame.display.set_caption(f"Backgammon {title}")
    
    # listener = threading.Thread(target=listen_loop)
    # listener.daemon = True
    # listener.start()
    
    # game_loop(screen, font)    
connect_to_server()