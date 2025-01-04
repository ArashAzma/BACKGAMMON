import socket
import pickle
import time
from utils.key2 import * 
from utils.constants import * 
from utils.helper import * 
from utils.constants import * 
from game.board import *
import ast
import threading
import pygame
import sys
import random

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

messages = []
input_text = ""

board = Board()
is_my_turn = False
current_roll = None
moves_left = 0
selected_piece = None

triangle_width = WINDOW_SIZE // 13
triangle_height = (BOARD_SIZE - 40) // 2

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
    opponent= (SERVER, int(port))
    message = f"{my_address};{opponent}"
    choose_opoonent_msg = create_message(MessageType.ACCEPT.value, message)
    client_socket.send(encrypt_server_message(choose_opoonent_msg, public_keys))
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
        
        time.sleep(1)

        data = client_socket.recv(BUFFER_SIZE)
        data = decrypt_server_message(data, private_keys)
        protocol, data = parse_client_message(data)
        if protocol == MessageType.REQUESTS.value:
            clients = pickle.loads(data)
            if requests != clients :
                requests = clients
                show_requests(requests, my_address)
        global opponent
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
                    opponent = dataAccept[0]
                    state = None    
                    alone = False
            
            time.sleep(1)
            
            dataDecline = decrypt_server_message(dataDecline, private_keys)
            protocol, dataDecline = parse_client_message(dataDecline)
            if protocol == MessageType.ANYACCEPTRES.value:
                dataDecline = pickle.loads(dataDecline)
                if dataDecline != [] :
                    print('declined :', dataDecline)
                    state = None    

def draw_board(screen):
    pygame.draw.rect(screen, BROWN, (0, 0, WINDOW_SIZE, BOARD_SIZE))
    
    for i in range(13):
        if(i==6): 
            continue
        x = (i * triangle_width)
        color = BEIGE if i % 2 == 0 else BLACK
        pygame.draw.polygon(screen, color, [
            (x, 0),
            (x + triangle_width, 0),
            (x + triangle_width/2, triangle_height)
        ])
        
        color = BEIGE if i % 2 == 1 else BLACK
        pygame.draw.polygon(screen, color, [
            (x, BOARD_SIZE),
            (x + triangle_width, BOARD_SIZE),
            (x + triangle_width/2, BOARD_SIZE - triangle_height)
        ])
        
def draw_pieces(screen):
    for space, count in board.myBoard.items():
        if count != 0:
            piece_radius = PIECE_RADIUS
            if space > 11:
                x = ((space - 11) * triangle_width) - triangle_width / 2
            else:
                x = ((13 - space) * triangle_width) - triangle_width / 2
            if(space >= 6 and space<=11):
                x -= triangle_width
            if(space >= 18):
                x += triangle_width
            color = WHITE if count > 0 else GRAY
            abs_count = abs(count)
            
            for i in range(abs_count):
                if space > 11:  
                    y = (i * (piece_radius * 2)) + piece_radius
                else:
                    y = BOARD_SIZE - (i * (piece_radius * 2)) - piece_radius
                
                pygame.draw.circle(screen, color, (x, y), piece_radius)

def draw_dice(screen, font):
    if current_roll:
        dice_size = 40
        x_offset = WINDOW_SIZE - 100
        y_offset = BOARD_SIZE // 2
        
        for i, roll in enumerate(current_roll):
            pygame.draw.rect(screen, WHITE, (x_offset, y_offset + (i * 50), dice_size, dice_size))
            text = font.render(str(roll), True, BLACK)
            screen.blit(text, (x_offset + 15, y_offset + (i * 50) + 10))

def draw_chat(screen, font):
    chat_surface = pygame.Surface((WINDOW_SIZE, CHAT_HEIGHT))
    chat_surface.fill(WHITE)
    
    y_offset = 10
    for message in messages[-5:]:
        if message.startswith("You:"):
            message = message[4:]
            x_offset = WINDOW_SIZE / 3 * 2
        else:
            message = message[9:]
            x_offset = 10
            
        text_surface = font.render(message, True, BLACK)
        chat_surface.blit(text_surface, (x_offset, y_offset))
        y_offset += FONT_SIZE + 5

    input_box = pygame.Rect(10, CHAT_HEIGHT - 40, WINDOW_SIZE - 20, 30)
    pygame.draw.rect(chat_surface, WHITE, input_box)
    pygame.draw.rect(chat_surface, BLACK, input_box, 2)
    
    input_surface = font.render(input_text, True, BLACK)
    chat_surface.blit(input_surface, (15, CHAT_HEIGHT - 35))
    
    screen.blit(chat_surface, (0, BOARD_SIZE))

def get_clicked_space(pos):
    x, y = pos
    if y >= BOARD_SIZE:
        return None
    if (x < WINDOW_SIZE /2):
        x += triangle_width
        
    space = 12 - (x) // triangle_width
    if space < 0 or space >= 24:
        return None
    
    if y < BOARD_SIZE // 2:
        space = 23 - space
        
    return space

def handle_click(opp_socket, pos):
    global selected_piece, moves_left, current_roll
    if not is_my_turn or not current_roll:
        return
        
    space = get_clicked_space(pos)
    if space is not None:
        if selected_piece is None:
            selected_piece = space
        else:
            steps = abs(space - selected_piece)
            if steps in current_roll:
                success, message = board.makeMove(selected_piece, my_color, steps)
                if success:
                    moves_left -= steps
                    current_roll.remove(steps)
                    if moves_left == 0:
                        end_turn(opp_socket)
                messages.append(f"System: {message}")
            selected_piece = None

def roll_dice():
    global current_roll, moves_left
    choose_opoonent_msg = create_message(MessageType.ROLL_DICE.value, '')
    client_socket.sendall(encrypt_server_message(choose_opoonent_msg, public_keys))
    data = client_socket.recv(BUFFER_SIZE)
    data = decrypt_server_message(data, private_keys)
    protocol, data = parse_client_message(data)
    message = pickle.loads(data)
    current_roll = message
    moves_left = sum(current_roll)

def end_turn(opp_socket):
    global is_my_turn, current_roll, moves_left
    is_my_turn = False
    current_roll = None
    moves_left = 0
    send_game_state(opp_socket)

def send_game_state(opp_socket):
    if opponent:
        game_state = {
            'board': board.myBoard,
            'turn_end': True
        }
        opp_socket.sendall(pickle.dumps(game_state))

def game_loop(opp_socket, screen, font):
    global input_text, messages, is_my_turn, my_color

    clock = pygame.time.Clock()
    
    if my_address[1] > opponent[1]:
        is_my_turn = True
        my_color = 'WHITE'
        roll_dice()
    else:
        is_my_turn = False
        my_color = 'BLACK'
        

    while True:
        screen.fill(WHITE)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                handle_click(opp_socket, event.pos)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if input_text.lower() == "q":
                        pygame.quit()
                        sys.exit()
                    opp_socket.send(pickle.dumps(f"CHAT:{input_text}"))
                    messages.append(f"You: {input_text}")
                    input_text = ""
                elif event.key == pygame.K_BACKSPACE:
                    input_text = input_text[:-1]
                else:
                    input_text += event.unicode

        draw_board(screen)
        draw_pieces(screen)
        draw_dice(screen, font)
        draw_chat(screen, font)

        pygame.display.flip()
        clock.tick(30) 

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
                print(f"Opponent: {message[5:]}")
                messages.append(f"Opponent: {message[5:]}")
                
    except Exception as e:
        messages.append(f"Error: {str(e)}")

def get_opp_message(opp_socket):
    print("Connected to opp!")
    while True:
        try:
            data = opp_socket.recv(BUFFER_SIZE)
            if not data:
                break
            handle_network_message(data)
        except ConnectionResetError:
            print("Opp connection closed.")
            break
    opp_socket.close()

def send_message(opp_socket):
    while True :
        message = input("> ")
        opp_socket.send(pickle.dumps(f"CHAT:{message}"))
        
def handshake():
    global my_address, private_keys, public_keys, opponent, opp_socket

    port = find_my_port()
    client_socket.connect((SERVER, port))
    my_address = client_socket.getsockname()

    print(f' MY ADDRESS {my_address} --- MY NODE PORT {port}')
    
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
        
    return True
        
def connect_to_server():
    global my_address, opp_socket, alone, opponent
    message = create_message("connect", my_address)
    client_socket.sendall(encrypt_server_message(message, public_keys))
    time.sleep(0.1)
    requestListener = threading.Thread(target=requestListen)
    requestListener.daemon = True
    requestListener.start()
    
    while (alone) :
        word = input()
        match word :
            case MessageType.REQUEST.value :
                send_request()
            case MessageType.ACCEPT.value :
                accept()
            case MessageType.DECLINE.value : 
                decline()
    
    try:
        opp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if type(opponent) == str :
            opponent = ast.literal_eval(opponent)
        opp_socket.connect(opponent)
        threading.Thread(target=get_opp_message, args=(opp_socket,), daemon=True).start()
    except:
        listener_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener_socket.bind(my_address)
        listener_socket.listen(1)
        print("Waiting for opponent to connect...")
        opp_socket, opp_address = listener_socket.accept()
        print(f"Opponent connected: {opp_address}")
        threading.Thread(target=get_opp_message, args=(opp_socket,), daemon=True).start()
        
    return True
    
def start_game():
    global my_address, opp_socket, alone, opponent
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
    font = pygame.font.Font(None, FONT_SIZE)
    title = "BLACK"
    if my_address[1] > opponent[1]:
        title = "WHITE"
        
    pygame.display.set_caption(f"Backgammon {title}")
    game_loop(opp_socket, screen, font)

def start_client():
    if handshake():
        if connect_to_server():
            start_game()
    
start_client()