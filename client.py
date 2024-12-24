import socket
import threading
import sys
from time import sleep
import pickle
import pygame
from utils.key import *  
from utils.constants import * 

client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client_socket.bind((SERVER, 0)) 
my_address = client_socket.getsockname()

state = None
alone = True
opponent = None
opponent_port = None

messages = []
input_text = ""

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
    global input_text, messages

    clock = pygame.time.Clock()

    while True:
        screen.fill(WHITE)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
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

        y_offset = 10
        for message in messages[-5:]:
            if message.startswith("You:"):
                message = message[4:]
                x_offset = WINDOW_SIZE / 3 * 2
            else:
                message = message[9:]
                x_offset = 10
                
            text_surface = font.render(message, True, BLACK)
            screen.blit(text_surface, (x_offset, y_offset))
            y_offset += FONT_SIZE + 5

        input_box = pygame.Rect(20, 140, WINDOW_SIZE-40, 20)
        pygame.draw.rect(screen, GRAY, input_box)
        pygame.draw.rect(screen, BLACK, input_box, 2)

        input_surface = font.render(input_text, True, BLACK)
        screen.blit(input_surface, (input_box.x + 5, input_box.y + 5))

        pygame.display.flip()
        clock.tick(30)  

def run_client():
    global opponent
    
    print(f'\nMy Address {my_address} \n')
    if connect_through_onion():
    
        pygame.init()
        screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
        font = pygame.font.Font(None, FONT_SIZE)
        listener = threading.Thread(target=listen_loop)
        listener.daemon = True
        listener.start()
        game_loop(screen, font)
    
run_client()
