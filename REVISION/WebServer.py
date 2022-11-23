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
clients = {} #dictionary for storing connection:username pairs this is everyone connected to the server
messages = [] #list of messages
inGroup = {} #dictionary for storing connection:username pairs this is everyone that has joined the group
oldestMessage = {} #dictionary for storing pairs between connections and the id of the oldest message they're allowed to view

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
                        if message not in clients.values():
                        #if not clients.get(message):
                            clients[connection] = message
                            connection.send(("Username set successfully. Welcome, " + message).encode())
                            #broadcast the new user + username to the entire chat room
                            if connection not in inGroup:
                                inGroup[connection] = clients[connection]
                                oldMess = len(messages) - 2
                                if oldMess < 0:
                                    oldMess = 0
                                oldestMessage[connection] = oldMess
                                broadcast("New user " + clients[connection] + " has entered the chat room!", connection, False)
                                #lets send the previous 2 messages
                                i = 1
                                if len(messages) > 0:
                                    prevMessages = "Previous Two Message:\n"
                                    while (i <= 2) and (len(messages) - i >= 0):
                                        addMessage = messages[len(messages) - i]
                                        message_to_send = "Message ID: " + str(len(messages) - i) + " Sender: " + addMessage["sender"] + " Time: " + addMessage["datetime"].strftime("%H:%M") + " Subject: " + addMessage["subject"]
                                        prevMessages += (message_to_send + '\n')
                                        i += 1
                                    connection.send(prevMessages.encode())      
                                #send the clients list
                                clientStr = "Users in the room: \n"
                                for client in clients.values():
                                    clientStr += client + "\n"
                                connection.send(clientStr.encode())

                                # send the list of groups as well
                                groupStr = "Here is a list of groups:\n Group Name: First, Group ID: 1\n Group Name: Second, Group ID: 2\n Group Name: Third, Group ID: 3\n Group Name: Fourth, Group ID: 4\n Group Name: Fifth, Group ID: 5\n"
                                connection.send(groupStr.encode())
                        else:
                            connection.send("That username is taken. Please try again.".encode())
                    else:
                        connection.send("Please enter a username first!".encode())
                #user joining the chat
                elif message.split(' ')[0] == "JOIN":
                    if connection not in inGroup:
                        inGroup[connection] = clients[connection]
                        oldMess = len(messages) - 2
                        if oldMess < 0:
                            oldMess = 0
                        oldestMessage[connection] = oldMess
                        broadcast("New user " + clients[connection] + " has entered the chat room!", connection, False)
                        #lets send the previous 2 messages
                        i = 1
                        if len(messages) > 0:
                            prevMessages = "Previous Two Messages:\n"
                            while (i <= 2) and (len(messages) - i >= 0):
                                addMessage = messages[len(messages) - i]
                                message_to_send = "Message ID: " + str(len(messages) - i) + " Sender: " + addMessage["sender"] + " Time: " + addMessage["datetime"].strftime("%H:%M") + " Subject: " + addMessage["subject"]
                                prevMessages += (message_to_send + '\n')
                                i += 1
                            connection.send(prevMessages.encode())      
                        #send the clients list
                        clientStr = "Users in the room: \n"
                        for client in clients.values():
                            clientStr += client + "\n"
                        connection.send(clientStr.encode())

                        # send the list of groups as well
                        groupStr = "Here is a list of groups:\n Group Name: First, Group ID: 1\n Group Name: Second, Group ID: 2\n Group Name: Third, Group ID: 3\n Group Name: Fourth, Group ID: 4\n Group Name: Fifth, Group ID: 5\n"
                        connection.send(groupStr.encode())
                    else:
                        connection.send(("You have already joined the message board").encode())
                #user posting a new message
                elif message.split(' ')[0] == "POST":
                    if connection in inGroup:
                        newMessage = {
                                "sender": clients[connection],
                                "datetime": datetime.datetime.now(),
                                "subject": message.split(' ')[1],
                                "content": ' '.join(message.split(' ')[2:])
                                }
                        messages.append(newMessage)

                        #broadcast the message to everyone else in the room
                        message_to_send = "Message ID: " + str(len(messages)-1) + " Sender: " + clients[connection] + " Time: " + newMessage["datetime"].strftime("%H:%M") + " Subject: " + newMessage["subject"]
                        broadcast(message_to_send, connection, True)
                    else:
                        connection.send("You must join the group using the JOIN command before posting".encode())
                #user requesting a message with an ID
                elif message.split(' ')[0] == "MESSAGE":
                    if connection in inGroup:
                        if int(message.split(' ')[1]) >= oldestMessage[connection]:
                            if int(message.split(' ')[1]) < len(messages):
                                connection.send(("Content: " + messages[int(message.split(' ')[1])]["content"]).encode())
                            else:
                                connection.send("No such message exists with that ID.".encode())
                        else:
                            connection.send("You are not allowed to view the requested message".encode())
                    else:
                        connection.send("You must join the group using the JOIN command before recieving content from board".encode())
                #user requesting to leave the group
                elif message.split(' ')[0] == "LEAVE":
                    if connection in inGroup:
                        del inGroup[connection]
                        del oldestMessage[connection]
                        broadcast(clients[connection] + " left the chat.", connection, False)
                    else:
                        connection.send("You already aren't in the group".encode())
                #user requesting list of users
                elif message.split(' ')[0] == "USERS":
                    if connection in inGroup:
                        clientStr = "Users in the room: \n"
                        for client in inGroup.values():
                            clientStr += client + "\n"
                        connection.send(clientStr.encode())
                    else:
                        connection.send("You aren't in the group you can't recieve a list of users".encode())
                #user requesting list of groups
                elif message.split(' ')[0] == "GROUPS":
                    groupStr = "Here is a list of groups:\n Group Name: First, Group ID: 1\n Group Name: Second, Group ID: 2\n Group Name: Third, Group ID: 3\n Group Name: Fourth, Group ID: 4\n Group Name: Fifth, Group ID: 5\n"
                    connection.send(groupStr.encode())

                #user requesting to join a group
                elif message.split(' ')[0] == "GROUPJOIN":
                    roomString = message.split(' ')[1]
                    room = 5
                    if roomString == 'First' or roomString == '1':
                        room = 0
                    elif roomString == 'Second' or roomString == '2':
                        room = 1
                    elif roomString == 'Third' or roomString == '3':
                        room = 2
                    elif roomString == 'Fourth' or roomString == '4':
                        room = 3
                    elif roomString == 'Fifth' or roomString == '5':
                        room = 4
                    else:
                        connection.send("Invalid group Name/ID.".encode())
                    if room in [0,1,2,3,4]:
                        if connection not in roomClients[room].keys():
                            userJoinedGroupMessage = "New user " + clients[connection] + " joined group " + str(room + 1) + "!"
                            roomClients[room][connection] = clients[connection]
                            groupBroadcast(userJoinedGroupMessage, connection, room, False)
                            connection.send(("You joined group " + str(room + 1)).encode())
                            #lets send the previous 2 messages from this group
                            i = 1
                            if len(roomMessages[room]) > 0:
                                prevMessages = "Previous Two Messages from group: " + str(room + 1) + "\n"
                                while (i <= 2) and (len(messages) - i >= 0):
                                    addMessage = roomMessages[room][len(roomMessages[room]) - i]
                                    message_to_send = "Message ID: " + str(len(roomMessages[room]) - i) + " Sender: " + addMessage["sender"] + " Time: " + addMessage["datetime"].strftime("%H:%M") + " Subject: " + addMessage["subject"]
                                    prevMessages += (message_to_send + '\n')
                                    i += 1
                                connection.send(prevMessages.encode())
                            #send list of users in group when you join
                            clientStr = "Users in group " + str(room + 1) + ": \n"
                            for client in roomClients[room].values():
                                clientStr += client + "\n"
                            connection.send(clientStr.encode())
                        else:
                            connection.send("You are already a member of this group.".encode())
                #user is posting to a group
                elif message.split(' ')[0] == "GROUPPOST":
                    roomString = message.split(' ')[1]
                    room = 5
                    if roomString == 'First' or roomString == '1':
                        room = 0
                    elif roomString == 'Second' or roomString == '2':
                        room = 1
                    elif roomString == 'Third' or roomString == '3':
                        room = 2
                    elif roomString == 'Fourth' or roomString == '4':
                        room = 3
                    elif roomString == 'Fifth' or roomString == '5':
                        room = 4
                    else:
                        connection.send("Invalid group Name/ID.".encode())
                    if room in [0,1,2,3,4]:
                        if connection in roomClients[room].keys():
                            newMessage = {
                                "sender": clients[connection],
                                "datetime": datetime.datetime.now(),
                                "subject": message.split(' ')[2],
                                "content": ' '.join(message.split(' ')[3:])
                                }
                            roomMessages[room].append(newMessage)

                            #broadcast the message to everyone else in the group
                            message_to_send = "This message is from group: " + str(room + 1) + "\n"
                            message_to_send += "Message ID: " + str(len(roomMessages[room])-1) + " Sender: " + clients[connection] + " Time: " + newMessage["datetime"].strftime("%H:%M") + " Subject: " + newMessage["subject"]
                            groupBroadcast(message_to_send, connection, room, True)
                        else:
                            connection.send("You are not in this group".encode())
                    
                #user is getting message from group
                elif message.split(' ')[0] == "GROUPMESSAGE":
                    roomString = message.split(' ')[1]
                    room = 5
                    if roomString == 'First' or roomString == '1':
                        room = 0
                    elif roomString == 'Second' or roomString == '2':
                        room = 1
                    elif roomString == 'Third' or roomString == '3':
                        room = 2
                    elif roomString == 'Fourth' or roomString == '4':
                        room = 3
                    elif roomString == 'Fifth' or roomString == '5':
                        room = 4
                    else:
                        connection.send("Invalid group Name/ID.".encode())
                    if room in [0,1,2,3,4]:
                        if connection in roomClients[room].keys():
                            if int(message.split(' ')[2]) < len(roomMessages[room]):
                                connection.send(("Content: " + roomMessages[room][int(message.split(' ')[2])]["content"]).encode())
                            else:
                                connection.send("No such message exists with that ID.".encode())
                        else:
                            connection.send("You are not in this group".encode())

                #user requests to leave a group
                elif message.split(' ')[0] == "GROUPLEAVE":
                    roomString = message.split(' ')[1]
                    room = 5
                    if roomString == 'First' or roomString == '1':
                        room = 0
                    elif roomString == 'Second' or roomString == '2':
                        room = 1
                    elif roomString == 'Third' or roomString == '3':
                        room = 2
                    elif roomString == 'Fourth' or roomString == '4':
                        room = 3
                    elif roomString == 'Fifth' or roomString == '5':
                        room = 4
                    else:
                        connection.send("Invalid group Name/ID.".encode())
                    if room in [0,1,2,3,4]:
                        if connection in roomClients[room].keys():
                            del roomClients[room][connection]
                            groupBroadcast(clients[connection] + " left group " + str(room + 1), connection, room, False)  
                        else:
                            connection.send("You are not in this group".encode())

                #user requests list of users in specified group
                elif message.split(' ')[0] == "GROUPUSERS":
                    roomString = message.split(' ')[1]
                    room = 5
                    if roomString == 'First' or roomString == '1':
                        room = 0
                    elif roomString == 'Second' or roomString == '2':
                        room = 1
                    elif roomString == 'Third' or roomString == '3':
                        room = 2
                    elif roomString == 'Fourth' or roomString == '4':
                        room = 3
                    elif roomString == 'Fifth' or roomString == '5':
                        room = 4
                    else:
                        connection.send("Invalid group Name/ID.".encode())
                    if room in [0,1,2,3,4]:
                        if connection in roomClients[room].keys():
                            clientStr = "Users in group " + str(room + 1) + ": \n"
                            for client in roomClients[room].values():
                                clientStr += client + "\n"
                            connection.send(clientStr.encode())
                        else:
                            connection.send("You are not in this group".encode())
                else:
                    # broken connection, remove the client
                    remove(connection)
            except:
                continue
 
# broadcast to all connected clients except the one that sent the message
def broadcast(message, connection, sendToConnection):
    print(message)
    for client in inGroup:
        if sendToConnection:
            try:
                client.send(message.encode())
                print(message)
            except:
                client.close()
        else:
            if client != connection:
                try:
                    client.send(message.encode())
                    print(message)
                except:
                    client.close()
 
                    # if the link is broken, we remove the client
                    remove(client) # can we get rid of this line?

def groupBroadcast(message, connection, room, sendToConnection):
    for client in roomClients[room]:
        if sendToConnection:
            try:
                client.send(message.encode())
                print(message)
            except:
                client.close()
        else:
            if client != connection:
                try:
                    client.send(message.encode())
                    print(message)
                except:
                    client.close()
 
                    # if the link is broken, we remove the client
                    remove(client) # can we get rid of this line?

def remove(connection):
    for i in range((len(roomClients) - 1)):
        if connection in roomClients[i].keys():
            del roomClients[i][connection]
            groupBroadcast(clients[connection] + " left group " + str(i + 1), connection, i, False) 
    if connection in inGroup:
        #print(clients[connection] + " left the chat.")
        del inGroup[connection]
        del oldestMessage[connection]
        broadcast(clients[connection] + " left the chat.", connection, False) 
    if connection in clients:
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