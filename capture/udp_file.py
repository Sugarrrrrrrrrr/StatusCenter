from capture.get_udp import get_udp_from_file, get_udp_from_network
from socket import socket, AF_INET, SOCK_DGRAM


class PcapFile(object):
    def __init__(self, filename='../data/test.pcap', ip_list=['192.168.1.4'], port=14550):
        self.guff = get_udp_from_file(filename=filename, ip_list=ip_list, port=port)

        self.buf = bytearray()
        self.buf_index = 0

    def buf_len(self):
        return len(self.buf) - self.buf_index

    def read(self, n):
        while self.buf_len() < n:
            s = next(self.guff)
            self.buf.extend(s)

        mbuf = self.buf[self.buf_index: self.buf_index + n]
        self.buf_index += n

        if self.buf_len() == 0:
            self.buf = bytearray()
            self.buf_index = 0

        return mbuf

    def close(self):
        del self.guff

    def write(self):
        pass

class multi_mav_udp(object):
    def __init__(self, filename='192.168.1.0', ip_list=['192.168.1.4'], port=14550):
        self.guff = get_udp_from_network(filename=filename, ip_list=ip_list, port=port)

        self.buf = bytearray()
        self.buf_index = 0

        self.udpsocket = socket(AF_INET, SOCK_DGRAM)
        self.addr_list = []
        self.addr_got = 0

    def buf_len(self):
        return len(self.buf) - self.buf_index

    def read(self, n):
        while self.buf_len() < n:
            s = next(self.guff)
            self.get_socket(s[1])
            self.buf.extend(s[0])

        mbuf = self.buf[self.buf_index: self.buf_index + n]
        self.buf_index += n

        if self.buf_len() == 0:
            self.buf = bytearray()
            self.buf_index = 0

        return mbuf

    def close(self):
        del self.guff

    def write(self, buf):
        if len(self.addr_list):
            for addr in self.addr_list:
                print(buf, addr)
                self.udpsocket.sendto(buf, addr)


    def get_socket(self, src_addr):
        #if not src_addr in self.addr_list:
        #    self.addr_list.append(src_addr)
        #    self.addr_got += 1
        self.addr_list = [src_addr]


if __name__ == '__main__':
    f = PcapFile()


