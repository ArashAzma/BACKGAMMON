# BACKGAMMON

---
# WireShark 🦈

## Handshake

- ### [PRIVATE KEY 0]
#### The user communicates with the first router:
  
![alt text](images/image.png)

#### The router sends a success message back to the user:
  
![alt text](images/image-2.png)

- ### [PRIVATE KEY 1]
#### The user sends encrypted chunks to the first router:

![alt text](images/image-6.png)

#### The first router assembles the chunks, decrypts them, and forwards the data to the second router.
#### second router recieving the key
  
![alt text](images/image-8.png)

#### sending success back to user
![alt text](images/image-7.png)

- ### [PRIVATE KEY 2]

#### The user sends encrypted chunks to the first router, which now contains twice the amount of encryption:
![alt text](images/image-9.png)

#### The second router receives the decrypted chunks from the first router:
![alt text](images/image-11.png)

#### The last router receives its private key:
![alt text](images/image-12.png)

#### The router sends a success message back to the user:
![alt text](images/image-10.png)

- ### [CONNECTING TO SERVER]

#### last router to Server
![alt text](images/image-1.png)

---
## Players Talking to eachother

### Chatting to eachother
![alt text](images/image-13.png)

#### Players with port numbers 61945 and 61848 engage in peer-to-peer (P2P) chat:

![alt text](images/image-14.png)

### Sending the board to eachother

#### player1 sending the board to player2 after making a move

![alt text](images/image-15.png) 

#### using this structure
```
    game_state = {
        "board": board.myBoard,
        "xJail": board.xJail,
        "oJail": board.oJail,
        "xFree": board.xFree,
        "oFree": board.oFree,
        "turn_end": True
    }
```
---
## Rolling the Dice

#### first create a message with roll dice Protocoll

```
    choose_opoonent_msg = create_message(MessageType.ROLL_DICE.value, '')
```

#### and then encrypt it with 3 layers of encryption

![alt text](images/image-16.png)

## Ending the game

When players have 15 Free pieces it will send a message with the board using a FINISHED_GAME protocoll. It well then wait for a response. The server analysis the board and sends a message to the client based on the board state.
If the game has ended the player sends a message to other player and they disconnect. 
