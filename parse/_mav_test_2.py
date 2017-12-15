import mavutil
import dialects.v10.ardupilotmega


def main():
    pass
    


if __name__ == '__main__':
    mf = mavutil.mavlink_connection('../data/test.pcap', ip_list=['192.168.1.4'])
    mf2 = mavutil.mavlink_connection('../data/test.pcap', ip_list=['192.168.1.5'])

    m = mf.recv_msg()
    m2 = mf2.recv_msg()
    i = 1
    while mf and mf2:
        print(m)
        print(m2)
        i+=1
        m = mf.recv_msg()
        m2 = mf2.recv_msg()

        if i%10==0:
            print(i)
            input()
