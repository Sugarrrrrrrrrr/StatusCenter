from parse import mavutil
from capture.udp_file import multi_mav_udp
from capture.get_udp import get_udp_from_network


if __name__ == '__main__':
    #f = multi_mav_udp(filename='10.168.103.0', ip_list=['10.168.103.72'], port=53)

    mf = mavutil.mavlink_connection('network:10.168.103.0', ip_list=['10.168.103.72'], port=53)
    
    mf.f.read(10)
