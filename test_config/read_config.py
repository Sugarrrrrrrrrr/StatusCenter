import json


if __name__ == '__main__':
    with open('.config', 'r') as f:
        j = json.load(f)

        uavs = j['uavs']
        for uav in uavs:
            connect_type = uav['type']
            name = uav['name']
            ip = uav['ip']
            port = uav['port']
            icon = uav['icon']

            network = '.'.join(ip.split('.')[:-1]) + '.0'

            print('udp:' + ip + ':' + str(port))
