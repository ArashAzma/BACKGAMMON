import socket
import pickle
import time
from utils.key2 import * 
from utils.constants import * 
from utils.helper import * 
import threading

state = None
alone = True
connected_to_opponent = False
opponent = None
is_accepter = None
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
my_address = ""
messages = []

def generate_client_keys():
    private_keys = []
    public_keys = []
    
    for i in range(3):
        node_private, node_public = generate_keys()
        private_keys.append(node_private)
        public_keys.append(node_public)
        
    return private_keys, public_keys
private_keys, public_keys = generate_client_keys()

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

def decline():
    print("enter the port you wanna decline :")
    port = input()
    opponent_address = (SERVER, int(port))
    message = f"{my_address};{opponent_address}"
    choose_opoonent_msg = create_message(MessageType.DECLINE.value, message)
    client_socket.send(encrypt_server_message(choose_opoonent_msg, public_keys))

def accept() :
    global alone, opponent, opp_socket, connected_to_opponent, is_accepter
    print("enter the port you wanna accept :")
    port = input()
    opp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    opp_socket.bind((SERVER, 0))
    opp_socket.listen(1)
    my_game_address = opp_socket.getsockname()
    print('my_game_address', my_game_address)
    
    opponent_address = (SERVER, int(port))
    message = f"{my_address};{opponent_address};{my_game_address}"
    choose_opoonent_msg = create_message(MessageType.ACCEPT.value, message)
    client_socket.send(encrypt_server_message(choose_opoonent_msg, public_keys))
    # opponent = (SERVER, int(port))
    alone = False
    
    
    while not connected_to_opponent:
        conn, addr = opp_socket.accept()
        print('CONNECTED TO OPPOENT', addr)
        connected_to_opponent = True
        is_accepter = True
        opponent = conn
        time.sleep(0.2)

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
    global client_socket, requested, private_keys, alone, state, opponent, connected_to_opponent, opp_socket, is_accepter
    requests = []
    onlines = []
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
                requests = clients
                show_requests(requests, my_address)
        
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
                    print('accepted :', dataAccept[0])
                    opponent = eval(dataAccept[0])
                    print("POPPP", opponent)
                    state = None
                    
                    opp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    opp_socket.connect(opponent)
                    print('Connected to ', opponent)
                    
                    connected_to_opponent = True
                    alone = False
                    is_accepter = False
                    break
            
            time.sleep(0.2)
            
            dataDecline = decrypt_server_message(dataDecline, private_keys)
            protocol, dataDecline = parse_client_message(dataDecline)
            
            if protocol == MessageType.ANYACCEPTRES.value:
                dataDecline = pickle.loads(dataDecline)
                if dataDecline != [] :
                    print('declined :', dataDecline)
                    state = None

def handle_network_message(data):
    global board, is_my_turn
    try:
        message = pickle.loads(data)
        if isinstance(message, dict):
            if 'board' in message:
                pass
                # board.myBoard = message['board']
                # if message.get('turn_end', False):
                #     is_my_turn = True
                #     roll_dice()
        elif isinstance(message, str):
            if message.startswith('CHAT:'):
                print(f"Opponent: {message[5:]}")
                messages.append(f"Opponent: {message[5:]}")
                
    except Exception as e:
        messages.append(f"Error: {str(e)}")

def listen_loop(buffer_size=BUFFER_SIZE):
    global messages, opp_socket, opponent, is_accepter
    while True:
        if opp_socket is None:
            continue
        try:
            if is_accepter:
                data = opponent.recv(buffer_size)  
            else:
                data = opp_socket.recv(buffer_size)  
            handle_network_message(data)
            # print(data)
            time.sleep(0.2)
        except Exception as e:
            messages.append(f"Listen error: {e}")
            break

def send_message():
    global opp_socket, opponent, is_accepter
    try:
        while True:
            message = input("> ")
            if message.lower() == 'q':
                break
            if is_accepter:
                opponent.sendall(pickle.dumps(f"CHAT:{message}")) 
            else:
                opp_socket.sendall(pickle.dumps(f"CHAT:{message}"))
    except KeyboardInterrupt:
        pass
    finally:
        opp_socket.close()

def connect_to_server():
    global my_address, connected_to_opponent
    port = find_my_port()
    client_socket.connect((SERVER, port))
    my_address = client_socket.getsockname()

    print(f' MY ADDRESS {my_address} --- MY NODE PORT {port}')
    
    global private_keys, public_keys

    #! Send private key 0
    client_socket.sendall(serialize_private_key(private_keys[0]))
    
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

    data = client_socket.recv(BUFFER_SIZE)
    protocol, message = parse_message(data)
    print('PRIVATE KEY 2 was a SUCCESS:', message)
    
    #! Send public keys
    for i, pk in enumerate(public_keys):
        client_socket.sendall(serialize_public_key(pk))
        data = client_socket.recv(BUFFER_SIZE)
        protocol, message = parse_message(data)
        print(f'PUBLIC KEY {i} was a SUCCESS:', message)
    

    message = create_message("connect", my_address)
    client_socket.sendall(encrypt_server_message(message, public_keys))
    time.sleep(0.1)
    requestListener = threading.Thread(target=requestListen)
    requestListener.daemon = True
    requestListener.start()
    
    global alone 
    while (alone) :
        if connected_to_opponent:
            break
        word = input()
        match word :
            case MessageType.REQUEST.value :
                send_request()
            case MessageType.ACCEPT.value :
                accept()
            case MessageType.DECLINE.value : 
                decline()
                
    if connected_to_opponent:
        listener = threading.Thread(target=listen_loop)
        listener.daemon = True
        listener.start()
        
        send_message()
    
connect_to_server()