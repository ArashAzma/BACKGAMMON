import socket
import threading
import sys
from utils.key import *  

SERVER_PORT = 5053
ONION_PORT = 6001
ONION_PORT_OPPONENT = 6004
BUFFER_SIZE = 1024
server_host = socket.gethostbyname(socket.gethostname())

client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client_socket.bind((server_host, 0)) 
my_address = client_socket.getsockname()
    
def listen_loop(buffer_size=BUFFER_SIZE):
    while True:
        try:
            data, addr = client_socket.recvfrom(buffer_size)
            print(f"\rOpponent: {data.decode()}\n> ", end='')
        except Exception as e:
            print(f"Listen error: {e}")
            break
        
def send_message(opponent):
    try:
        while True:
            message = input("> ")
            if message.lower() == 'q':
                break
            
            client_socket.sendto(message.encode(), opponent)
    except KeyboardInterrupt:
        pass
    finally:
        client_socket.close()
        sys.exit(0)

def create_onion_message(message, destination):
    current_message = f"{destination[0]}:{destination[1]}:0:{message}".encode()
    
    for key in reversed(RELAY_KEYS):
        print(f'Message: {current_message.hex()[:20]}')
        current_message = encrypt_message(key, current_message)
    
    return current_message


def create_onion_message_opponent(me, opponent):
    current_message = f"{me}:{opponent}".encode()
    
    for key in reversed(RELAY_KEYS):
        print(f'Message: {current_message.hex()[:20]}')
        current_message = encrypt_message(key, current_message)
    
    return current_message

def connect_through_onion():
    server_address  = (server_host, SERVER_PORT)
    first_relay = (server_host, ONION_PORT)
    first_relay_opponent = (server_host, ONION_PORT_OPPONENT)
    
    connection_msg = create_onion_message(my_address, server_address)
    
    client_socket.sendto(connection_msg, first_relay)
    
    data, addr = client_socket.recvfrom(BUFFER_SIZE)
    
    for key in (RELAY_KEYS):
        data = decrypt_message(key, data)
    
    data = data.decode()
    if data == 'ready':
        print("Connected to server through onion network...")
        print("choose your opponent")
        
        # get opponent port that he wanna connect to
        opponent_port = input()
        # meke a meesage of ports combined(his port and opponent port)
        choose_opoonent_msg = create_onion_message_opponent(my_address[1], opponent_port)
        client_socket.sendto(choose_opoonent_msg, first_relay_opponent)
        
        data, addr = client_socket.recvfrom(BUFFER_SIZE)
        opponent_data = data.decode()
        opponent_address, opponent_port, _ = opponent_data.split(' ')
        opponent = (opponent_address, int(opponent_port))
        print(f"ME {my_address} -- OPPONENT{opponent}")
        
        return opponent, first_relay
    else:
        raise ConnectionError("Failed to connect through onion network")

def run_client(server_host=server_host, server_port=SERVER_PORT):
    opponent, first_relay = connect_through_onion()
    
    listener = threading.Thread(target=listen_loop)
    listener.daemon = True
    listener.start()
    
    send_message(opponent)

run_client()
