from scToolbox import LinkManager
from scToolbox import scToolbox
from scApplication import scApplication
from parse import mavutil
from capture.udp_file import multi_mav_udp

import sys, time, random

from socket import *

class udp_send():
    def __init__(self, port=14550):
        self.port = port

        self.udpCliSock = socket(AF_INET, SOCK_DGRAM) 
        
    def send(self, data, host):
        addr = (host, self.port)
        self.udpCliSock.sendto(data, addr)

    def __del__(self):
        self.udpCliSock.close()


def msg_x_y(m, x, y):
    return mf.mav.gps_raw_int_encode(m.time_usec, m.fix_type, m.lat+x, m.lon+y, m.alt, m.eph, m.epv, m.vel, m.cog, m.satellites_visible)
    

if __name__ == '__main__':
    #app = scApplication(sys.argv)
    #app.initForNormalAppBoot()

    mf = mavutil.mavlink_connection('data/test.pcap', ip_list=['192.168.1.4'])
    
    
    b = b"\xfe\x1e\x18\x01\x01\x18\x00\x00\x00\x00\x00\x00\x00\x00\x933\xc5\r\x84\xca\x8aC\x96&\x02\x00\x0f'\xff\xff\x00\x00\x00\x00\x01\x00|\xd6"
    b_heartbeat = b'\xfe\t{\x01\x01\x00\x00\x00\x00\x00\x02\x03Q\x03\x03"\r'
    m = mf.mav.decode(bytearray(b))
    m_heartbeat = mf.mav.decode(bytearray(b_heartbeat))
    m_t = m

    us = udp_send()

    N = 100000 #- 99999
    for i in range(N):
        n1 = 10
        n2 = 100
        if i % n1 == 0:
            m1 = msg_x_y(m, i*5, i*5)
            us.send(m1.pack(mf.mav), '192.168.42.128')
            
            m2 = msg_x_y(m, -i*5-100, -i*5)
            us.send(m2.pack(mf.mav), '192.168.42.255')
            print(i/n1)
        if i % n2 == 0:
            us.send(b_heartbeat, '192.168.42.128')
            us.send(b_heartbeat, '192.168.42.255')

    #for i in range(100):
    #    udp_send(str(time.time()).encode('utf-8'))

    print('-----')
