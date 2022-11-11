# Python program to implement client side of chat room.
import socket
import sys
from threading import *
 
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ip = "127.0.0.1"
port = 9999

def send_message():
    while True:
        try:
            # wait for command line input
            message = sys.stdin.readline()

            if message:
                # encode the message and send it to the server
                server.send(message.encode())
                print("<You> " + message)
        except:
            continue

def receive_message():
    while True:
        try:
            # receive bytes from the server
            # TODO: server needs to send the username as well
            message, addr = server.recvfrom(2048)

            # logic for client to get username here
            if message.decode("UTF-8") == "Welcome to this chatroom!":
                username = input("Please enter a username: ")
                server.send(("CLIENT_USERNAME "+username).encode())
                print("<You> " + username)
            print("<> " + message)
        except:
            continue

# start both threads so we can listen for server messages and send our own commands 
Thread(target=receive_message).start()
Thread(target=send_message).start()

server.connect((ip, port))