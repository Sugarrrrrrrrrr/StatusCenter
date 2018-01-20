from parse import mavutil
from capture.udp_file import multi_mav_udp

import sys, time, random


def requestDataStream(mavfile, stream, start_stop=1, rate=10):  # MAV_DATA_STREAM stream
    msg = mavfile.mav.request_data_stream_encode(
        1,  # target_system
        1,  # target_component
        stream,  # req_stream_id
        rate,  # req_message_rate
        start_stop  # start_stop                : 1 to start sending, 0 to stop sending. (uint8_t)
    )
    mavfile.mav.send(msg)

if __name__ == '__main__':

    ip = '192.168.1.2'
    port = 14555
    mf = mavutil.mavlink_connection('udp:' + ip + ':' + str(port))

    print('requestDataStream(mf, 1)')
    print('requestDataStream(mf, 1, 0)')
    l = [1, 2, 3, 6, 10, 11, 12]
    print(l)
