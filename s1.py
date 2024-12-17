import socket

SERVER = socket.gethostbyname(socket.gethostname())
SERVER_PORT = 5052
BUFFER_SIZE = 128

server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.bind((SERVER, SERVER_PORT))

clients = []
def start():
    print(f"Server is listening on {SERVER}")
    
    while True:
        data, address = server.recvfrom(BUFFER_SIZE)
        print(f"Connection from [{address}]")
        if address not in clients:
            clients.append(address)
            server.sendto(b'ready', address)
        
        if len(clients) == 2: 
            break
        
start()

print(f"Clients:\n\t{clients}")  
print("Got 2 clients")

client1 = clients.pop()
client2 = clients.pop()

client1_add, client1_port = client1
client2_add, client2_port = client2

server.sendto(f"{client1_add} {client1_port} {SERVER_PORT}".encode(), client2)
server.sendto(f"{client2_add} {client2_port} {SERVER_PORT}".encode(), client1)
