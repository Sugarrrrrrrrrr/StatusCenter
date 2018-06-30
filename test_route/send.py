#!/usr/bin/env python

from socket import *

# HOST = '127.0.0.1'
HOST = '192.168.1.199'
PORT = 15551
BUFSIZE = 1024

ADDR = (HOST, PORT)

udpCliSock = socket(AF_INET, SOCK_DGRAM)

for i in range(100):
    data = input('>')
    #data = '%2d:hello' % i
    if not data:
        break
    udpCliSock.sendto(data.encode('utf-8'), ADDR)
    

udpCliSock.close()
