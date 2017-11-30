from capture.get_udp import get_udp_from_file


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

if __name__ == '__main__':
    f = PcapFile()


