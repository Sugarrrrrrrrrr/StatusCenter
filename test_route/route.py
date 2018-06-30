#!/usr/bin/env python
# -*- coding:UTF-8 -*-

from socket import *
import time
from time import ctime
import _thread


def route_check(HOST='192.168.1.199', PORT = 15551, BUFSIZE = 1024):

    ADDR = (HOST, PORT)
    udpSerSock = socket(AF_INET, SOCK_DGRAM)
    udpSerSock.bind(ADDR)

    filename = str(int(time.time())) + '_' + str(PORT) + '.txt'
    f = open(filename, 'w')

    r = ''


    while True:
        data, addr = udpSerSock.recvfrom(BUFSIZE)
        try:
            data = str(data, encoding='utf-8')[:-6]
        except Exception as e:
            continue

        ls = data.split('\n')
        data = '\n'.join([l[:-6] for l in ls])

        if data != r:
            print(data)
            print("port:", PORT)
            r = data
        
            print (time.asctime(), file=f)
            print(data, file=f)
            print('----------\n', file=f)
            f.flush()

            print('----- wait for next -----')

    f.close()
    udpSerSock.close()

if __name__ == '__main__':
    ports = [15551, 15552, 15553, 15555, 15560]

    for port in ports:
        _thread.start_new_thread(route_check, ('192.168.1.199', port,))

    while 1:
        pass
