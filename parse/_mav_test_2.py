import mavutil
import dialects.v10.ardupilotmega


def main():
    pass
    


if __name__ == '__main__':
    mf = mavutil.mavlink_connection('../data/test.pcap')

    m = mf.recv_msg()
    i = 1
    while mf:
        print(m)
        i+=1
        m = mf.recv_msg()

        if i%10==0:
            print(i)
            input()
