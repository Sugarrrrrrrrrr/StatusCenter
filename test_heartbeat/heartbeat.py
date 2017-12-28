import sys
sys.path.append('..')

from parse import mavutil


if __name__ == '__main__':
    mav = mavutil.mavlink_connection('udp:192.168.4.2:14550')
