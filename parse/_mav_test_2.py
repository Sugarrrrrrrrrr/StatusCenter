import mavutil
import dialects.v10.ardupilotmega


def main():
    pass
    


if __name__ == '__main__':
    mf = mavutil.mavlink_connection('../data/test.pcap', ip_list=['192.168.1.4'])

    m = mf.recv_msg()

