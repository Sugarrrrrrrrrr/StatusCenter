import ctypes
import winpcapy
import threading
import socket
import dpkt
import random
import struct

class SyslogSenderWinPcap:
    '''
    原理：先产生一个ping包，以获取本机、网关的MAC地址，然后通过WinPcap发包
    限制：目前不能发送给本机，但可以实现；仅支持数据链路层为以太网的情况
    '''
    
    def __init__(self, dst, dport, src = None, sport = 10000):

        self.dst = dst
        self.dport = dport
        self.src = src
        self.sport = sport
        
        self.errbuf= ctypes.create_string_buffer(winpcapy.winpcapy_types.PCAP_ERRBUF_SIZE)
        
        interface = self.ChooseDevice()

        self.fp = winpcapy.winpcapy_types.pcap_open_live(interface, 65536, winpcapy.winpcapy_types.PCAP_OPENFLAG_PROMISCUOUS, 1000, self.errbuf)
        
        if not self.fp:
            print('Fatal error: open interface %s failed' % interface)
            exit(-1)
            
        if winpcapy.winpcapy_types.pcap_datalink(self.fp) != winpcapy.winpcapy_types.pcap_datalink_name_to_val(b'EN10MB'):
            print('Fatal error: unsupported datalink layer')
            exit(-1)
        
        self.GetEthernetHeader()
        
    def ChooseDevice(self):
        interface = ctypes.POINTER(winpcapy.winpcapy_types.pcap_if_t)()
        if -1 == winpcapy.winpcapy_types.pcap_findalldevs(ctypes.byref(interface), self.errbuf):
            print('Fatal error: no device')
            exit(-1)
            
        alldevs = []
        while interface:
            alldevs.append((interface.contents.name, interface.contents.description))
            
            interface = interface.contents.next
           
        while True: 
            index = 0
            for dev in alldevs:
                index += 1
                print ('%d.' % index)
                print ('%s %s' % dev)
                
            selected = input('Enter the interface number (1-%d):' % index)
            
            try:
                index = int(selected)
            except TypeError:
                print('Integer expect')
                continue
            
            if index < 1 or index > len(alldevs):
                print('Too big or too small')
                continue
            
            return alldevs[index - 1][0]
        
    # 发送IP包
    def Send(self, ip_packet):
        e = dpkt.ethernet.Ethernet(
            data = ip_packet,
            dst = self.dst_mac,
            src = self.src_mac)
        
        to_send = eval(str(e))
        
        buf = (ctypes.c_ubyte * len(to_send))(*to_send)
        winpcapy.winpcapy_types.pcap_sendpacket(self.fp, buf, len(buf))
        return e, buf, to_send
        
    def GetEthernetHeader(self):
        # 抓包过滤
        bpf = ctypes.pointer(winpcapy.winpcapy_types.bpf_program())
        winpcapy.winpcapy_types.pcap_compile(self.fp, bpf, ('icmp and host %s' % self.dst).encode(), 1, 0)
        winpcapy.winpcapy_types.pcap_setfilter(self.fp, bpf)
        
        # 抓包回调
        def _packet_handler(param, header, pkt_data):
            s = bytearray(pkt_data[:header.contents.len])
            # s = ''.join([chr(b) for b in pkt_data[:header.contents.len]])
            e = dpkt.ethernet.Ethernet(s)
            
            # 获取本机MAC和网关MAC
            self.dst_mac = e.dst
            self.src_mac = e.src
        
        packet_handler = winpcapy.winpcapy_types.pcap_handler(_packet_handler)
        
        # 产生一个ping包
        def ToGenPing():
            self.GenPing(self.dst)
        
        t = threading.Timer(0.5, ToGenPing)
        t.start() # 输出ping包，以便获得以太网包头

        winpcapy.winpcapy_types.pcap_loop(self.fp, 1, packet_handler, None)

    def GenPing(self, dst):
        import random
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
            
            icmp = dpkt.icmp.ICMP(
                type=8, data=dpkt.icmp.ICMP.Echo(id=random.randint(0, 0xffff),
                                                     seq=1, data='Hello'))
            #sock.connect((ip, 1))
            #sock.sendall(str(icmp))
    
            sock.sendto(icmp.pack_hdr() + icmp.data.pack_hdr() + icmp.data.data.encode(), (dst, 1))
        except socket.error as e:
            print('Fatal error: (%d) %s' % (e.errno, e.message))
            exit(-1)
        #finally:
            #sock.close()

    def MacAddress(self, s):
        return struct.pack('BBBBBB', *[int(i, 16) for i in s.split('-')])
        
    def Process(self, msg):
        u = dpkt.udp.UDP()
        u.sport = self.sport
        u.dport = self.dport
        u.data = msg
        u.ulen = len(u)
    
        #print u.sum
    
        i = dpkt.ip.IP(data = u)
        #i.off = dpkt.ip.IP_DF # frag off
        i.p = dpkt.ip.IP_PROTO_UDP
        i.src = socket.inet_aton(self.src) 
        i.dst = socket.inet_aton(self.dst)
        i.len = len(i)
        
        e, buf, to_send = self.Send(i)
        return i, e, buf, to_send

if __name__ == '__main__':
    s = SyslogSenderWinPcap('192.168.42.128', 14550, '192.168.42.22', 22222)
    i, e, buf, to_send = s.Process(b'hiiiiiiiiiiiiiii')
