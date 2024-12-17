import socket
import threading
import sys

SERVER = '10.0.0.1'
SERVER_PORT = 5052
BUFFER_SIZE = 128

rendezvous = (SERVER, SERVER_PORT)

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

client.sendto(b'0', rendezvous)

data = client.recv(1024).decode()
if data == 'ready':
    print("Connected To the Server...")
    
data = client.recv(1024).decode()
opponent_address, opponent_port, server_port = data.split(' ')
print(f"\nOpponent {opponent_address}:{opponent_port}\nServer Port: {server_port}")


OPPONENT = (opponent_address, int(opponent_port))

def listen():
    while True:
        data, addr = client.recvfrom(1024)
        print(f"\rOpponent: {data.decode()}\n> ", end='')

def exit():
    client.close()
    sys.exit(0)

listener = threading.Thread(target=listen, args=())
listener.start()


while True:
    message = input("> ")
    if(message == 'q'):
        exit()
        break
    client.sendto(message.encode(), OPPONENT)