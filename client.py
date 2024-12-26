import socket
import threading
import sys
from time import sleep
import pickle
import pygame
from utils.key import *  
from utils.constants import * 
from game.board import *
import random

client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client_socket.bind((SERVER, 0)) 
my_address = client_socket.getsockname()

state = None
alone = True
opponent = None
opponent_port = None

messages = []
input_text = ""

board = Board()
is_my_turn = False
current_roll = None
moves_left = 0
selected_piece = None

triangle_width = WINDOW_SIZE // 13
triangle_height = (BOARD_SIZE - 40) // 2

def create_onion_message(message, message_type: MessageType=None):
    if message_type is None:
        current_message = f"{message}".encode()
    else:
        current_message = f"{message}:{message_type.value}".encode()
    
    for key in reversed(RELAY_KEYS):
        # print(f'Message: {current_message.hex()[:20]}')
        current_message = encrypt_message(key, current_message)
    
    return current_message

def send_request(first_relay_opponent) :
    global opponent_port, state
    state = "waiting"
    opponent_port = input()
    message = f"{my_address[1]}:{opponent_port}"
    choose_opoonent_msg = create_onion_message(message, MessageType.REQUEST)
    client_socket.sendto(choose_opoonent_msg, first_relay_opponent)

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
    choose_opoonent_msg = create_onion_message("decline", None)
    client_socket.sendto(choose_opoonent_msg, (SERVER, 6006))
    return

def accept() :
    global alone, opponent, requested
    choose_opoonent_msg = create_onion_message("accept", None)
    client_socket.sendto(choose_opoonent_msg, (SERVER, 6006))
    opponent_port = requested
    opponent = (SERVER, int(opponent_port))
    alone = False
    return

def requestListen() :
    global client_socket, requested
    while alone:
        data, _ = client_socket.recvfrom(BUFFER_SIZE)
        data = decrypt_onion_message(data)
        
        data1, data2 = data.split(':')[-2:]
        if data1 == "request": 
            print('==========You Got a request==========')
            print('Do you wanna play with', data2.split("with ")[-1])
            requested = data2.split("with ")[-1]   
        elif data1 == "ans":
            get_ans(data2)
    
def show_online_users(clients):
    users = clients.copy()
    users.remove(my_address)
            
    if(len(users) > 0):
        print('\nOnline players:')
        for client in users:
            print('\t',client[1])
    else:
        print('Nobody is online')

def decrypt_onion_message(data, requires_decode=True):
    for key in (RELAY_KEYS):
        data = decrypt_message(key, data)
        
    if requires_decode:
        data = data.decode()
    return data

def connect_through_onion():
    global opponent, state
    first_relay = (SERVER, ONION_PORT)
    first_relay_opponent = (SERVER, ONION_PORT)
    
    message = f"{my_address}"
    connection_msg = create_onion_message(message, MessageType.CONNECT)
    
    client_socket.sendto(connection_msg, first_relay)
    
    data, _ = client_socket.recvfrom(BUFFER_SIZE)
    data = decrypt_onion_message(data)
    if data == 'ready':
        print("Connected to server through onion network...")
        data, _ = client_socket.recvfrom(BUFFER_SIZE)
        data = decrypt_onion_message(data, False)
        clients = pickle.loads(data)
        show_online_users(clients)
    
        requestListener = threading.Thread(target=requestListen)
        requestListener.daemon = True
        requestListener.start()
        
        # get opponent port that he wanna connect to
        while alone :
            state = input()
            match state:
                case "request":
                    print("choose your opponent")
                    send_request(first_relay_opponent)
                    while state == "waiting" :
                        sleep(0.1)
                case "accept":
                    accept()
                case "decline":
                    decline()
       
       
        print(f"ME {my_address} -- OPPONENT{opponent}")
        return first_relay
    else:
        raise ConnectionError("Failed to connect through onion network")

# BOARD
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

def handle_click(pos):
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
                success, message = board.makeMove(selected_piece, not is_my_turn, steps)
                if success:
                    moves_left -= steps
                    current_roll.remove(steps)
                    if moves_left == 0:
                        end_turn()
                messages.append(f"System: {message}")
            selected_piece = None

def roll_dice():
    global current_roll, moves_left
    roll1 = random.randint(1, 6)
    roll2 = random.randint(1, 6)
    current_roll = [roll1, roll2]
    if roll1 == roll2:
        current_roll *= 2
    moves_left = sum(current_roll)

def end_turn():
    global is_my_turn, current_roll, moves_left
    is_my_turn = False
    current_roll = None
    moves_left = 0
    send_game_state()

def send_game_state():
    if opponent:
        game_state = {
            'board': board.myBoard,
            'turn_end': True
        }
        client_socket.sendto(pickle.dumps(game_state), opponent)

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
            data = data.decode()
            if data.startswith("CHAT:"):
                received_message = data[5:]
                messages.append(f"Opponent: {received_message}")
        except Exception as e:
            messages.append(f"Listen error: {e}")
            break
        
def send_message(opponent):
    try:
        while True:
            message = input("> ")
            if message.lower() == 'q':
                break
            client_socket.sendto(f"CHAT:{message}".encode(), opponent)
    except KeyboardInterrupt:
        pass
    finally:
        client_socket.close()
        sys.exit(0)
        
def game_loop(screen, font):
    global input_text, messages, is_my_turn

    clock = pygame.time.Clock()
    
    if my_address[1] > opponent[1]:
        is_my_turn = True
        roll_dice()

    while True:
        screen.fill(WHITE)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                handle_click(event.pos)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if input_text.lower() == "q":
                        pygame.quit()
                        sys.exit()
                    client_socket.sendto(f"CHAT:{input_text}".encode(), opponent)
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

def run_client():
    global opponent
    # opponent = (SERVER, 123123)
    
    print(f'\nMy Address {my_address} \n')
    if connect_through_onion():
        pygame.init()
        screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
        font = pygame.font.Font(None, FONT_SIZE)
        title = "BLACK"
        if my_address[1] > opponent[1]:
            title = "WHITE"
            
        pygame.display.set_caption(f"Backgammon {title}")
        
        listener = threading.Thread(target=listen_loop)
        listener.daemon = True
        listener.start()
        
        game_loop(screen, font)
    
run_client()
