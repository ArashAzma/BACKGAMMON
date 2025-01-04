def create_message(protocol, message):
    return f"{protocol}:{message}".encode()

def parse_message(data):
    decoded_data = data.decode()
    protocol, message = decoded_data.split(":", 1)
    return protocol, message

def create_client_message(message_type: str, payload: bytes) -> bytes:
    header = message_type.encode()
    return header + b":" + payload

def parse_client_message(message: bytes) -> tuple[str, bytes]:
    header, payload = message.split(b":", 1)
    return header.decode(), payload

def show_online_users(clients, my_address):
    users = clients.copy()
    users.remove(f'{my_address}')
    print('\nOnline players:')
    if(len(users) > 0):
        for client in users:
            client =  eval(client)
            print('\t',client[1])
    else:
        print('Nobody is online')
        
def show_requests(clients, my_address):
    result = []
    for item in clients:
        parts = item.split(';')
        for part in parts:
            part = part.strip()
            if part:  
                result.append(eval(part))
    
    users = result.copy()
    users.remove(my_address)
    print('\nRequests :')
    if(len(users) > 0):
        for client in users:
            print('\t',client[1])
    else:
        print('You have no requests!')