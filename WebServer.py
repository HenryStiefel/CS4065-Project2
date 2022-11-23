import socket
import select
import sys
from _thread import *
import datetime
import time
 
# initialize server information, start the server and listen for up to 100 connections
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
 
ip = "127.0.0.1"
port = 9999

server.bind((ip, port))
server.listen(100)
 
# we need to access these variables in all threads, so make them global
global clients
global messages
clients = {} #dictionary for storing connection:username pairs
messages = [] #list of messages

# keep separate list of connections for each room (this will be a list of lists, the interior list has connection:username pairs)
roomClients = [
    {},
    {},
    {},
    {},
    {}
]

# keep separate list of messages for each room (this will be a list of lists, the interior list has message objects)
roomMessages = [
    [],
    [],
    [],
    [],
    []
] 
 
def clientthread(connection, address):
 
    # sends a message to the client connection
    connection.send("Please enter a username with the \"USERNAME [your username here]\" command.".encode())
 
    while True:
            try:
                #listen for input from the connection
                message = connection.recv(2048).decode("UTF-8")
                
                #if the sending user doesn't have an actual username yet, make them get one
                if clients[connection] == "NewUser":
                    # if the new connection sent a username command:
                    if message.split(' ')[0] == "USERNAME":
                        message = message.split(' ')[1]
                        if not clients.get(message):
                            clients[connection] = message
                            connection.send(("Username set successfully. Welcome, " + message).encode())
                            #broadcast the new user + username to the entire chat room
                            broadcast("New user " + clients[connection] + " has entered the chat room!", connection)

                            #lets send the previous 2 messages, other users, and rooms here
                            if len(messages) == 1:
                                message_to_send = "Message ID: " + str(len(messages)-1) + " Sender: " + messages[len(messages)-1]["sender"] + " Time: " + messages[len(messages)-1]["datetime"].strftime("%H:%M") + " Subject: " + messages[len(messages)-1]["subject"]
                                connection.send(message_to_send.encode())

                            elif len(messages) > 1:
                                message_to_send = "Message ID: " + str(len(messages)-1) + " Sender: " + messages[len(messages)-1]["sender"] + " Time: " + messages[len(messages)-1]["datetime"].strftime("%H:%M") + " Subject: " + messages[len(messages)-1]["subject"]
                                connection.send(message_to_send.encode())
                                message_to_send = "Message ID: " + str(len(messages)-2) + " Sender: " + messages[len(messages)-2]["sender"] + " Time: " + messages[len(messages)-2]["datetime"].strftime("%H:%M") + " Subject: " + messages[len(messages)-2]["subject"]
                                connection.send(message_to_send.encode())
                            
                            #send the clients list
                            clientStr = "Users in the room: "
                            for client in clients.values():
                                clientStr += "\n" + client
                            connection.send(clientStr.encode())

                            # send the list of groups as well
                            groupStr = "Here is a list of groups:\nGroup ID: 0\nGroup ID: 1\nGroup ID: 2\nGroup ID: 3\nGroup ID: 4"
                            connection.send(groupStr.encode())
                        else:
                            connection.send("That username is taken. Please try again.".encode())
                    else:
                        connection.send("Please enter a username first!".encode())

                #user posting a new message
                elif message.split(' ')[0] == "POST":
                    newMessage = {
                            "sender": clients[connection],
                            "datetime": datetime.datetime.now(),
                            "subject": message.split(' ')[1],
                            "content": ' '.join(message.split(' ')[2:])
                            }
                    messages.append(newMessage)

                    #broadcast the message to everyone else in the room
                    message_to_send = "Message ID: " + str(len(messages)-1) + " Sender: " + clients[connection] + " Time: " + newMessage["datetime"].strftime("%H:%M") + " Subject: " + newMessage["subject"]
                    broadcast(message_to_send, connection)

                #user requesting a message with an ID
                elif message.split(' ')[0] == "MESSAGE":
                    if int(message.split(' ')[1]) < len(messages):
                        connection.send(("Subject: " + messages[int(message.split(' ')[1])]["subject"] + " Date: " + messages[int(message.split(' ')[1])]["datetime"] + " Content: " + messages[int(message.split(' ')[1])]["content"]).encode())
                    else:
                        connection.send("No such message exists with that ID.".encode())
                
                #user requesting to see other users
                elif message.split(' ')[0] == "USERS":
                    clientStr = "Users in the room: "
                    for client in clients.values():
                        clientStr += "\n" + client
                    connection.send(clientStr.encode())

                # send the 5 preset group ids
                elif message.split(' ')[0] == "GROUPS":
                    groupStr = "Here is a list of groups:\nGroup ID: 0\nGroup ID: 1\nGroup ID: 2\nGroup ID: 3\nGroup ID: 4"
                    connection.send(groupStr.encode())

                # allow a user to join a group
                elif message.split(' ')[0] == "GROUPJOIN":
                    room = int(message.split(' ')[1])
                    userJoinedGroupMessage = "New user " + clients[connection] + " joined group " + str(room) + "!"
                    if room not in [0,1,2,3,4]:
                        connection.send("Invalid group ID.".encode())
                    elif connection not in roomClients[room].keys():
                        roomClients[room][connection] = clients[connection]
                        groupBroadcast(userJoinedGroupMessage, connection, 1)
                        connection.send(("You joined group " + str(room)).encode())
                    else:
                        connection.send("You are already a member of this group.".encode())

                # receive a group message
                elif message.split(' ')[0] == "GROUPPOST":
                    room = int(message.split(' ')[1])
                    if room not in [0,1,2,3,4]:
                        connection.send("Invalid group ID.".encode())
                    elif connection not in roomClients[room].keys():
                        connection.send("You are not a member of this group.".encode())
                    else:
                        newMessage = {
                            "sender": clients[connection],
                            "datetime": datetime.datetime.now(),
                            "subject": message.split(' ')[2],
                            "content": ' '.join(message.split(' ')[3:])
                            }
                        roomMessages[room].append(newMessage)

                        #broadcast the message to everyone else in the room
                        message_to_send = "Message ID: " + str(len(roomMessages[room])-1) + " Sender: " + clients[connection] + " Time: " + newMessage["datetime"].strftime("%H:%M") + " Subject: " + newMessage["subject"]
                        groupBroadcast(message_to_send, connection, room)

                # show all users in a group
                elif message.split(' ')[0] == "GROUPUSERS":
                    room = int(message.split(' ')[1])
                    if room not in [0,1,2,3,4]:
                        connection.send("Invalid group ID.".encode())
                    else:
                        usersStr = "Users in group " + str(room) + ":\n"
                        for client in roomClients[room].values():
                            usersStr = usersStr + client + '\n'
                        connection.send(usersStr.encode())
                
                # leave a group
                elif message.split(' ')[0] == "GROUPLEAVE":
                    room = int(message.split(' ')[1])
                    if room not in [0,1,2,3,4]:
                        connection.send("Invalid group ID.".encode())
                    elif connection not in roomClients[room].keys():
                        connection.send("You are not a member of this group.".encode())
                    else:
                        del roomClients[room][connection]
                        connection.send(("You left group " + str(room)).encode())
                        userLeftGroupStr = "User " + clients[connection] + " has left group " + str(room)
                        groupBroadcast(userLeftGroupStr, connection, room)

                # view a group message
                elif message.split(' ')[0] == "GROUPMESSAGE":
                    room = int(message.split(' ')[1])
                    if room not in [0,1,2,3,4]:
                        connection.send("Invalid group ID.".encode())
                    elif connection not in roomClients[room].keys():
                        connection.send("You are not a member of this group.".encode())
                    else:
                        if int(message.split(' ')[2]) < len(roomMessages[room]):
                            connection.send(("Subject: " + roomMessages[room][int(message.split(' ')[2])]["subject"] + "Date: " + roomMessages[room][int(message.split(' ')[2])]["datetime"] + " Content: " + roomMessages[room][int(message.split(' ')[2])]["content"]).encode())
                        else:
                            connection.send("No such message exists with that ID in that group.".encode())
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

def groupBroadcast(message, connection, roomID):
    print(message)
    for client in roomClients[roomID].keys():
        if client != connection:
            try:
                client.send(message.encode())
                print(message)
            except:
                client.close()
    
 
def remove(connection):
    if connection in clients:
        print(clients[connection] + " left the chat.")
        del clients[connection]

def testconnections():
    while True:
        #every 1 second, we will test every connection and make sure it is still there - if not, we can notify that it was removed from the chat room
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
    #listen for connecting clients
    conn, addr = server.accept()
 
    clients[conn] = "NewUser"
 
    # prints the address of the user that just connected
    # (this stays on server side right now, does not get broadcasted to other clients)
    print (addr[0] + " connected")
 
    # creates thread for every user
    start_new_thread(clientthread,(conn,addr)) 
 
conn.close()
server.close()