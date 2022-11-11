import socket
import select
import sys
from _thread import *
 
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
 
ip = "127.0.0.1"
port = 9999

server.bind((ip, port))
server.listen(100)
 
# TODO: make this a dictionary, map client-given username to connection
clients = {}
 
def clientthread(connection, address):
 
    # sends a message to the client connection
    connection.send("Welcome to this chatroom!".encode())
    print('sent welcome to client')
 
    while True:
            try:
                message = connection.recv(2048).decode("UTF-8")
                
                if message[:16] == "CLIENT_USERNAME ":
                    clients[conn] = message[17:]
                    broadcast("New user " + clients[conn] + " has entered the chat room!", connection)
                if message:
                    # print the message to the server terminal
                    print ("<" + address[0] + "> " + message)
 
                    # TODO: we need the client username here
                    message_to_send = "<" + address[0] + "> " + message
                    broadcast(message_to_send, connection)
                else:
                    # broken connection, remove the client
                    remove(connection)
            except:
                continue
 
# broadcast to all connected clients except the one that sent the message
def broadcast(message, connection):
    for client in clients:
        if client != connection:
            try:
                client.send(message)
            except:
                client.close()
 
                # if the link is broken, we remove the client
                remove(client) # can we get rid of this line?
 
def remove(connection):
    if connection in clients:
        clients.remove(connection)
 
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