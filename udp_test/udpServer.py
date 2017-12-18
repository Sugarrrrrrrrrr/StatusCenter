#!/usr/bin/env python
# -*- coding:UTF-8 -*-

from socket import *
from time import ctime

HOST = '10.168.103.72'
PORT = 14550
BUFSIZE = 1024

ADDR = (HOST, PORT)

udpSerSock = socket(AF_INET, SOCK_DGRAM)
udpSerSock.bind(ADDR)

while True:
    print('wating for message...')
    data, addr = udpSerSock.recvfrom(BUFSIZE)
    print(data)
    udpSerSock.sendto(('[%s] %s' % (ctime(), data)).encode('utf-8'), addr)
    print('...received from and retuned to:', addr)

udpSerSock.close()
