import pcap

if __name__ == '__main__':
    p = pcap.pcap('eth0')

    addr = lambda pkt, offset: '.'.join(str(pkt[i]) for i in range(offset, offset + 4))

    for ts, pkt in p:
        print('%d\tSRC %-16s\tDST %-16s' % (ts, addr(pkt, p.dloff + 12), addr(pkt, p.dloff + 16)))
