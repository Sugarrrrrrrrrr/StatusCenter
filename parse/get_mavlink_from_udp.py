import sys
sys.path.append('..')

from capture.get_udp_from_file import get_udp_from_file


def get_msgid(mavlink):
    if len(mavlink) >= 6:
        return mavlink[5]


def get_mavlink_from_udp(ip_list, port):

    buf = b''

    for data in get_udp_from_file(ip_list, port):

        mavlink = b''
        buf += data
        # print('[S]', len(buf), buf)

        fe_flag = False
        for i, b in enumerate(buf):
            if b == 0xfe:
                fe_flag = True
                buf = buf[i:]
                break
        if not fe_flag:
            buf = b''

        l_buf = len(buf)
        while l_buf >= 2:
            l_mavlink = buf[1]+8
            if l_buf >= l_mavlink:
                mavlink = buf[:l_mavlink]
                yield mavlink
                # print('[M]', len(mavlink), mavlink)

                buf = buf[l_mavlink:]
                l_buf = len(buf)
            else:
                break
        # print('[B]', len(buf), buf)
        # print('-----------------------')
        # input()


if __name__ == '__main__':
    ip_list = ['192.168.1.4']
    port = 14550

    for i, mavlink in enumerate(mavlink_from_udp(ip_list, port)):
        print(i, get_msgid(mavlink), mavlink)


