import socket
import select
import sys
from _thread import *
import datetime
import time
 
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
 
ip = "127.0.0.1"
port = 9999

server.bind((ip, port))
server.listen(100)
 
# TODO: make this a dictionary, map client-given username to connection
global clients
global messages
clients = {}
messages = []
 
def clientthread(connection, address):
 
    # sends a message to the client connection
    connection.send("Please enter a username with the \"USERNAME [your username here]\" command.".encode())

    #TODO: send the previous 2 messages
    #TODO: send a list of other usernames
 
    while True:
            try:
                message = connection.recv(2048).decode("UTF-8")
                
                if clients[connection] == "NewUser":
                    if message.split(' ')[0] == "USERNAME":
                        message = message.split(' ')[1]
                        if not clients.get(message):
                            clients[connection] = message
                            connection.send(("Username set successfully. Welcome, " + message).encode())
                            broadcast("New user " + clients[connection] + " has entered the chat room!", connection)

                            #lets send the previous 2 messages, other users, and rooms here
                            if len(messages) > 0:
                                print('.')
                                #SEND THE PREVIOUS 1 OR 2 MESSAGES
                            
                            #send the clients list
                            if len(clients) > 1:
                                clientListMessage = "Other users:\n"
                                for client in clients:
                                    # don't send the current connection though
                                    if client != connection:
                                        clientListMessage += (clients[client] + '\n')
                                connection.send(clientListMessage.encode())
                        else:
                            connection.send("That username is taken. Please try again.".encode())
                    else:
                        connection.send("Please enter a username first!".encode())
                elif message.split(' ')[0] == "POST":
                    newMessage = {
                            "sender": clients[connection],
                            "datetime": datetime.datetime.now(),
                            "subject": message.split(' ')[1],
                            "content": ' '.join(message.split(' ')[2:])
                            }
                    messages.append(newMessage)

                    message_to_send = "Message ID: " + str(len(messages)) + " Sender: " + clients[connection] + " Time: " + newMessage["datetime"].strftime("%H:%M") + " Subject: " + newMessage["subject"]
                    print(message_to_send)
                    broadcast(message_to_send, connection)
                elif message.split(' ')[0] == "MESSAGE":
                    if int(message.split(' ')[1]) < len(messages):
                        connection.send(("Content: " + messages[int(message.split(' ')[1])]["content"]).encode())
                    else:
                        connection.send("No such message exists with that ID.".encode())
                else:
                    # broken connection, remove the client
                    remove(connection)
            except:
                continue
 
# broadcast to all connected clients except the one that sent the message
def broadcast(message, connection):
    print(message)
    for client in clients:
        if client != connection:
            try:
                client.send(message.encode())
                print(message)
            except:
                client.close()
 
                # if the link is broken, we remove the client
                remove(client) # can we get rid of this line?
 
def remove(connection):
    if connection in clients:
        print(clients[connection] + " left the chat.")
        del clients[connection]

def testconnections():
    while True:
        time.sleep(1)
        try:
            for client in clients:
                try: 
                    client.sendall(b"ping")
                except:
                    remove(client)
        except:
            pass      

start_new_thread(testconnections, ())
 
while True:
    conn, addr = server.accept()
 
    clients[conn] = "NewUser"
 
    # prints the address of the user that just connected
    # (this stays on server side right now, does not get broadcasted to other clients)
    print (addr[0] + " connected")
 
    # creates thread for every user
    start_new_thread(clientthread,(conn,addr)) 
 
conn.close()
server.close()