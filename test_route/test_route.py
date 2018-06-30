#!/usr/bin/env python
# -*- coding:UTF-8 -*-

from socket import *
import time
from time import ctime

# HOST = '127.0.0.1'
HOST = '192.168.1.199'
PORT = 15560
# PORT = 15551
BUFSIZE = 2048

ADDR = (HOST, PORT)

udpSerSock = socket(AF_INET, SOCK_DGRAM)
udpSerSock.bind(ADDR)

filename = str(time.time()) + '.txt'
f = open(filename, 'w')


while True:
    data, addr = udpSerSock.recvfrom(BUFSIZE)
    print(data)
    print("addr:", addr)

    print (time.asctime(), file=f)
    print(str(data, encoding='utf-8'), file=f)
    print('----------\n', file=f)
    f.flush()

    print('press for next')

f.close()
udpSerSock.close()
