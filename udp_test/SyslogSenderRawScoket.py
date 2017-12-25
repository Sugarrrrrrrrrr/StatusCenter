import socket
import dpkt

class SyslogSenderRawScoket:
    def __init__(self, dst, dport, src, sport = 10000):
        self.dst = socket.gethostbyname(dst)
        self.dport = dport
        self.src = src
        self.sport = sport
        
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
        self.sock.connect((self.dst, 1))
        
    def Send(self, ip_packet):
        self.sock.sendall(eval(str(ip_packet)))

    def Process(self, msg):
        u = dpkt.udp.UDP()
        u.sport = self.sport
        u.dport = self.dport
        u.data = msg
        u.ulen = len(u)
    
        # IP 的 str 会触发 IP 的校验和计算，也会触发 TCP UDP 的校验和计算
        # TCP/UDP的校验和是： 源IP，目的IP，协议，TCP或UDP包（头+内容）
        #u.sum = ?
    
        i = dpkt.ip.IP(data = u)
        #i.off = dpkt.ip.IP_DF # frag off
        i.p = dpkt.ip.IP_PROTO_UDP
        i.src = socket.inet_aton(self.src) # xp sp2之后 禁止发送非本机IP地址的数据包；linux, server无限制
        i.dst = socket.inet_aton(self.dst)
        i.len = len(i)

        self.i = i
        
        self.Send(i)

if __name__ == '__main__':
    s = SyslogSenderRawScoket('192.168.42.1', 14550, '192.168.42.2', 22222)
    
