import sys
sys.path.append('..')


from get_mavlink_from_udp import get_mavlink_from_udp, get_msgid
#from mavprotocol import MAVLink, MAVError
from mavparse import MAVParseError
from dialects.v10.ardupilotmega import *


def main():
    ip_list = ['192.168.1.4']
    port = 14550

    m = None
    MAV = MAVLink(None)
    lat = None
    lon = None
    alt = None

    for i, mavlink in enumerate(get_mavlink_from_udp(ip_list, port)):
        #if get_msgid(mavlink) == 24:
            try:
                m = MAV.decode(mavlink)
            except MAVError as e:
                print(i, mavlink)
                print(type(e), ':', e)
                print('-------------')
                #input()
                continue
            #except Exception as e:
                #print(type(e), ':', e)
                #print('-------------')
                #input()
                #continue

            print(i, m.get_msgId(), m.get_type())
                

            for fieldname in m.fieldnames:
                exec('print(\'%s:\', m.%s)' % (fieldname, fieldname))

            print('-------------')

            #input()


if __name__ == '__main__':

    ip_list = ['192.168.1.4']
    port = 14550
    MAV = MAVLink(None)
    mavlinks = get_mavlink_from_udp(ip_list, port)

    mavlink = MAV.decode(next(mavlinks))

