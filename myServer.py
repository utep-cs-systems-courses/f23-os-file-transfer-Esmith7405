#! /usr/bin/env python3

# Echo server program

import socket, sys, re
sys.path.append("../lib")       # for params
import params
import mytar
import os

switchesVarDefaults = (
    (('-l', '--listenPort') ,'listenPort', 50001),
    (('-?', '--usage'), "usage", False), # boolean (set if present)
    )

progname = "echoserver"
paramMap = params.parseParams(switchesVarDefaults)

listenPort = paramMap['listenPort']
listenAddr = ''       # Symbolic name meaning all available interfaces

if paramMap['usage']:
    params.usage()

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((listenAddr, listenPort))
s.listen(1)              # allow only one outstanding request
# s is a factory for connected sockets

#open the tar file
fd = os.open(b"out.tar", os.O_WRONLY | os.O_CREAT)

conn, addr = s.accept()  # wait until incoming connection request (and accept it)
print('Connected by', addr)
while 1:
    data = conn.recv(1024).decode()
    if len(data) == 0:
        print("Zero length read, nothing to send, terminating")
        break

    #Write to an archive file
    os.write(fd, data)

    sendMsg = ("Echoing %s" % data).encode()
    print("Received '%s', sending '%s'" % (data, sendMsg.decode()))
    while len(sendMsg):
        bytesSent = conn.send(sendMsg)
        sendMsg = sendMsg[bytesSent:0]
conn.shutdown(socket.SHUT_WR)
conn.close()

#close out.tar for writing
os.close(fd)

#Untar the archive
fd = os.open(b"out.tar", os.O_RDONLY)
reader = mytar.TarReader(fd)
reader.Untar()
os.close(fd)