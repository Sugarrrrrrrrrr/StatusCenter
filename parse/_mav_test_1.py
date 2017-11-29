import sys
sys.path.append('..')


from mavlink_from_udp import mavlink_from_udp, get_msgid
from mavprotocol import MAVLink, MAVError
from mavparse import MAVParseError


def main():
    ip_list = ['192.168.1.4']
    port = 14550

    m = None
    MAV = MAVLink(None)
    lat = None
    lon = None
    alt = None

    for i, mavlink in enumerate(mavlink_from_udp(ip_list, port)):
        if get_msgid(mavlink) == 24:
            try:
                m = MAV.decode(mavlink)
            except MAVParseError as e:
                print(i, mavlink)
                print(type(e), ':', e)
                input()
            except Exception as e:
                print(type(e), ':', e)
                input()
            

            change = False

            if lat!=m.lat:
                print('lat change')
                change = True
                lat = m.lat
            if lon!=m.lon:
                print('lon change')
                change = True
                lon = m.lon
            if alt!=m.alt:
                print('alt change')
                change = True
                alt = m.alt

            if change:
                input()
                change = False
                

            for fieldname in m.fieldnames:
                exec('print(\'%s:\', m.%s)' % (fieldname, fieldname))

            #input()


if __name__ == '__main__':

    main()
        
