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
import threading

def generate_client_keys():
    private_keys = []
    public_keys = []
    
    for i in range(3):
        node_private, node_public = generate_keys()
        private_keys.append(node_private)
        public_keys.append(node_public)
        
    return private_keys, public_keys

state = None
alone = True
opponent = None
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
private_keys, public_keys = generate_client_keys()
my_address = ""

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
    
def decrypt_server_message(message, private_keys):
    for pk in private_keys:
        message = decrypt_message(message, pk)        
    return message

def encrypt_server_message(message, public_keys):
    for pk in reversed(public_keys):
        message = encrypt_message(message, pk)        
    return message

def get_ans(ans) :
    global state, opponent, opponent_port, alone
    if ans == "accepted" :
        opponent = (SERVER, int(opponent_port))
        client_socket.recvfrom(BUFFER_SIZE)
        alone = False
    else : 
        client_socket.recvfrom(BUFFER_SIZE)
        print("not accepted")
    state = None


def decline():
    print("enter the port you wanna decline :")
    port = input()
    opponent_address = (SERVER, int(port))
    message = f"{my_address};{opponent_address}"
    choose_opoonent_msg = create_message(MessageType.DECLINE.value, message)
    client_socket.send(encrypt_server_message(choose_opoonent_msg, public_keys))

def accept() :
    global alone, opponent
    print("enter the port you wanna accept :")
    port = input()
    opponent_address = (SERVER, int(port))
    message = f"{my_address};{opponent_address}"
    choose_opoonent_msg = create_message(MessageType.ACCEPT.value, message)
    client_socket.send(encrypt_server_message(choose_opoonent_msg, public_keys))
    opponent = (SERVER, int(port))
    alone = False


def send_request() :
    global opponent_port, state, my_address
    state = "waiting"
    print("enter your opponent port")
    port = input()
    opponent_address = (SERVER, int(port))
    message = f"{my_address};{opponent_address}"
    choose_opoonent_msg = create_message(MessageType.REQUEST.value, message)
    client_socket.send(encrypt_server_message(choose_opoonent_msg, public_keys))

def requestListen() :
    requests = []
    onlines = []
    global client_socket, requested, private_keys, alone, state
    print("im listening")
    while alone:
        message = f"{my_address}"
        choose_opoonent_msg = create_message(MessageType.ANYREQUEST.value, message)
        client_socket.sendall(encrypt_server_message(choose_opoonent_msg, public_keys))
        
        #get clients list
        data = client_socket.recv(BUFFER_SIZE)
        data = decrypt_server_message(data, private_keys)
        protocol, data = parse_client_message(data)
        if protocol == MessageType.ONLINES.value:
            clients = pickle.loads(data)
            if clients != onlines :
                show_online_users(clients, my_address)
                onlines = clients
        else:
            print('There was an Error with Clients')
        
        time.sleep(0.2)

        data = client_socket.recv(BUFFER_SIZE)
        data = decrypt_server_message(data, private_keys)
        protocol, data = parse_client_message(data)
        if protocol == MessageType.REQUESTS.value:
            clients = pickle.loads(data)
            if requests != clients :
                print('requests :', clients)
                requests = clients
        
        if state == "waiting" :        
            message = f"{my_address}"
            choose_opoonent_msg = create_message(MessageType.ANYACCEPT.value, message)
            client_socket.sendall(encrypt_server_message(choose_opoonent_msg, public_keys))
                
            dataAccept = client_socket.recv(BUFFER_SIZE)
            dataDecline = client_socket.recv(BUFFER_SIZE)
            
            dataAccept = decrypt_server_message(dataAccept, private_keys)
            protocol, dataAccept = parse_client_message(dataAccept)
            if protocol == MessageType.ANYACCEPTRES.value:
                dataAccept = pickle.loads(dataAccept)
                if dataAccept != [] :
                    print('accepted :', dataAccept)
                    state = None    #need to be changed!!!
            
            time.sleep(0.1)
            
            dataDecline = decrypt_server_message(dataDecline, private_keys)
            protocol, dataDecline = parse_client_message(dataDecline)
            if protocol == MessageType.ANYACCEPTRES.value:
                dataDecline = pickle.loads(dataDecline)
                if dataDecline != [] :
                    print('declined :', dataDecline)
                    state = None    #need to be changed!!!

def connect_to_server():
    CONNECTION_MODE = True
    global my_address
    port = find_my_port()
    client_socket.connect((SERVER, port))
    my_address = client_socket.getsockname()

    print(f' MY ADDRESS {my_address} --- MY NODE PORT {port}')
    
    global private_keys, public_keys

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
    

    message = create_message("connect", my_address)
    client_socket.sendall(encrypt_server_message(message, public_keys))
    print('Sent connect')
    time.sleep(0.1)
    requestListener = threading.Thread(target=requestListen)
    requestListener.daemon = True
    requestListener.start()
    
    global alone 
    while (alone) :
        word = input()
        match word :
            case MessageType.REQUEST.value :
                send_request()
            case MessageType.ACCEPT.value :
                accept()
            case MessageType.DECLINE.value : 
                decline()
    
connect_to_server()