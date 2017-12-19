from comm.LinkManager import LinkManager
from scToolbox import scToolbox
from scApplication import scApplication
from parse import mavutil

import sys, time

from socket import *

def udp_send(data, host):
    # host = '192.168.42.255'
    port = 14550
    addr = (host, port)
    udpCliSock = socket(AF_INET, SOCK_DGRAM)
    udpCliSock.sendto(data, addr)

def msg_x_y(m, x, y):
    return mf.mav.gps_raw_int_encode(m.time_usec, m.fix_type, m.lat+x, m.lon+y, m.alt, m.eph, m.epv, m.vel, m.cog, m.satellites_visible)
    

if __name__ == '__main__':

    
    
    #app = scApplication(sys.argv)
    #app.initForNormalAppBoot()

    mf = mavutil.mavlink_connection('data/test.pcap', ip_list=['192.168.1.4'])
    
    
    b = b"\xfe\x1e\x18\x01\x01\x18\x00\x00\x00\x00\x00\x00\x00\x00\x933\xc5\r\x84\xca\x8aC\x96&\x02\x00\x0f'\xff\xff\x00\x00\x00\x00\x01\x00|\xd6"
    m = mf.mav.decode(bytearray(b))

    for i in range(1000):
        #time.sleep(1)
        m1 = msg_x_y(m, -i*20, i*20)
        udp_send(m1.pack(mf.mav), '192.168.42.128')
        m2 = msg_x_y(m, i*20, i*20)
        udp_send(m2.pack(mf.mav), '192.168.42.255')
        print(i)


    #for i in range(100):
    #    udp_send(str(time.time()).encode('utf-8'))

    print('-----')

