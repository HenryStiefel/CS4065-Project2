# Python program to implement client side of chat room.
import socket
import sys
from threading import *
 
global server
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def send_message():
    while True:
        # need global stop_threads variable to stop threads blocking when main program exits
        global stop_threads
        if stop_threads:
            break

        try:
            # wait for command line input
            message = sys.stdin.readline().strip('\n').split(' ')

            # SEE COMMANDS
            if message[0] == "COMMANDS":
                print(
                    "CONNECT [address] [port]\n" +
                    "USERNAME\n" +
                    "JOIN [room id]\n" + 
                    "POST [subject] [content]\n" +
                    "USERS\n" +
                    "LEAVE\n" +
                    "MESSAGE [message id]\n" + 
                    "EXIT\n"
                )

            # CONNECT TO SERVER
            elif message[0] == "CONNECT":
                if len(message) == 3:
                    try:
                        connect(message[1], int(message[2]))
                    except:
                        print("Failed to connect to server.")
                else:
                    print("Invalid arguments.")

            # JOIN CHAT ROOM
            elif message[0] == "JOIN":
                if len(message) == 1:
                    server.send(' '.join(message).encode())
                else:
                    print("Invalid arguments.")

            # POST NEW MESSAGE
            elif message[0] == "POST":
                if len(message) >= 3:
                    server.send(' '.join(message).encode())
                else:
                    print("Invalid arguments.")
            # Get List of users in public chat room
            elif message[0] == "USERS":
                if len(message) == 1:
                    server.send(' '.join(message).encode())
                else:
                    print("Invalid arguments.")

            # LEAVE public message board
            elif message[0] == "LEAVE":
                if len(message) == 1:
                    server.send(' '.join(message).encode())
                else:
                    print("Invalid arguments.")

            # REQUEST MESSAGE BY ID
            elif message[0] == "MESSAGE":
                if len(message) == 2:
                    server.send(' '.join(message).encode())
                else:
                    print("Invalid arguments")

            # request list of groups
            elif message[0] == "GROUPS":
                if len(message) == 1:
                    server.send(' '.join(message).encode())
                else:
                    print("Invalid arguments")
            
            # request to join group
            elif message[0] == "GROUPJOIN":
                if len(message) == 2:
                    server.send(' '.join(message).encode())
                else:
                    print("Invalid arguments")

            # post message to group
            elif message[0] == "GROUPPOST":
                if len(message) >= 4:
                    server.send(' '.join(message).encode())
                else:
                    print("Invalid arguments")
            
            # get message from group
            elif message[0] == "GROUPMESSAGE":
                if len(message) == 3:
                    server.send(' '.join(message).encode())
                else:
                    print("Invalid arguments")

            # leave group
            elif message[0] == "GROUPLEAVE":
                if len(message) == 2:
                    server.send(' '.join(message).encode())
                else:
                    print("Invalid arguments")

            # request list of users in the group
            elif message[0] == "GROUPUSERS":
                if len(message) == 2:
                    server.send(' '.join(message).encode())
                else:
                    print("Invalid arguments")

            # LEAVE SERVER AND STOP CLIENT
            elif message[0] == "EXIT":
                stop_threads = True
                exit()

            # SET/INITIALIZE USERNAME
            elif message[0] == "USERNAME":
                # encode the message and send it to the server
                if len(message) == 2:
                    server.send(("USERNAME " + message[1]).encode())
                else:
                    print("Invalid arguments.")

            else:
                print("Invalid command, try again.")
        except:
            continue

def receive_message():
    while True:
        global stop_threads
        if stop_threads:
            break
        try:
            # receive bytes from the server
            message, addr = server.recvfrom(2048)

            if message:
                #disregard the ping sent every 1000ms testing if client still active
                if message.decode("UTF-8") != "ping":
                    print(message.decode("UTF-8"))
        except:
            continue

def connect(ip, port):
    server.connect((ip, port))
def exit():
    server.close()
    print('Left server.')

stop_threads = False

# start both threads so we can listen for server messages and send our own commands 
r = Thread(target=receive_message).start()
s = Thread(target=send_message).start()

print("To see a list of commands, please type \"COMMANDS\" (case sensitive)")

#server.connect((ip, port))