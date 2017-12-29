import sys
sys.path.append('..')

from parse import mavutil



if __name__ == '__main__':
    
    mf = mavutil.mavlink_connection('../data/waypoints_201712261521.pcap', ip_list=['192.168.4.1'])

    file = open('misson_msg_buffer.txt', 'w')
    m = mf.recv_msg()
    ms = []

    index = 1
    while True:
        if m.get_msgId() in [x for x in range(39, 48)]:

            ms.append(m)

            file.write('%4d:\t%3d\t%s %s\n' % (index, m.get_srcSystem(), m.get_type(), m.get_msgbuf()))

            index += 1

        try:
            m = mf.recv_msg()
        except Exception as e:
            print(e)
            break
        
    file.close()
    print(len(ms))
