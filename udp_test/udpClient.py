#!/usr/bin/env python

from socket import *

HOST = '192.168.42.128'
PORT = 14550
BUFSIZE = 1024

ADDR = (HOST, PORT)

udpCliSock = socket(AF_INET, SOCK_DGRAM)

while True:
    data = input('>')
    if not data:
        break
    udpCliSock.sendto(data.encode('utf-8'), ADDR)
    #data, ADDR = udpCliSock.recvfrom(BUFSIZE)
    #if not data:
    #    break
    #print(data)


udpCliSock.close()
