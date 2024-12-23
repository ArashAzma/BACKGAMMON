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

state = None
alone = True
opponent = None
opponent_port = None

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


def send_request (first_relay_opponent) :
    global opponent_port
    opponent_port = input()
    choose_opoonent_msg = create_onion_message_opponent(my_address[1], opponent_port)
    client_socket.sendto(choose_opoonent_msg, first_relay_opponent)
    return

def get_ans(ans) :
    global opponent, opponent_port, alone
    if ans == "accepted" :
        opponent = (server_host, opponent_port)
        alone = False
    else : 
        print("not accepted")
    return


def decline(first_relay_opponent):
    choose_opoonent_msg = create_onion_message_ans("decline")
    client_socket.sendto(choose_opoonent_msg, first_relay_opponent)
    return

def accept(first_relay_opponent) :
    global alone
    choose_opoonent_msg = create_onion_message_ans("accept")
    client_socket.sendto(choose_opoonent_msg,(server_host, 6007))
    print("i sent it to server")
    alone = False
    return

def requestListen () :
    global client_socket
    data, addr = client_socket.recvfrom(BUFFER_SIZE)
    print(f"Received data: {data} from {addr}")
    data = data.decode('utf-8')
    
    data1, data2 = data.split(':')[-2:]
    if data1 == "request":    
        print(data2)
    elif data1 == "ans":
        get_ans(data2)


def create_onion_message_opponent(me, opponent):
    current_message = f"{me}:{opponent}".encode()
    
    for key in reversed(RELAY_KEYS):
        print(f'Message: {current_message.hex()[:20]}')
        current_message = encrypt_message(key, current_message)
    
    return current_message

def create_onion_message_ans(ans):
    current_message = f"{ans}".encode()
    
    for key in reversed(RELAY_KEYS):
        print(f'Message: {current_message.hex()[:20]}')
        current_message = encrypt_message(key, current_message)
    
    return current_message


def connect_through_onion():
    global opponent
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
        requestListener = threading.Thread(target=requestListen)
        requestListener.daemon = True
        requestListener.start()
        
        # get opponent port that he wanna connect to
        while alone :
            state = input()
            if state == "request" :
                print("choose your opponent")
                send_request(first_relay_opponent)
            elif state == "accept" :
                accept(first_relay_opponent)
            elif state == "decline" :
                decline(first_relay_opponent)
        
        print(f"ME {my_address} -- OPPONENT{opponent}")
        
        return first_relay
    else:
        raise ConnectionError("Failed to connect through onion network")

def run_client(server_host=server_host, server_port=SERVER_PORT):
    first_relay = connect_through_onion()
    
    listener = threading.Thread(target=listen_loop)
    listener.daemon = True
    listener.start()
    
    send_message(opponent)

run_client()
