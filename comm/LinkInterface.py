import threading
from parse import mavutil


class LinkInterface(threading.Thread):
    def __init__(self, link_name, app, linkMgr):
        super().__init__()
        self.app = app
        self.link_name = link_name
        self.linkMgr = linkMgr

        self.marker_create = False
        self.uav_lat = None
        self.uav_lng = None
        self.message_recieved = 0

        self.js_result = None

        # link_name = uav1:10.168.103.72:14550
        # mav = mavutil.mavlink_connection('network:10.168.103.0', ip_list=['10.168.103.72'], port=53)
        list_link = link_name.split(':')
        self.uav_name = list_link[0]
        self.ip = list_link[1]
        self.port = eval(list_link[2])
        self.icon = list_link[3]

        list_ip = self.ip.split('.')
        self.network = '.'.join(list_ip[:-1]) + '.0'
        self.mav = mavutil.mavlink_connection('network:' + self.network, ip_list=[self.ip], port=self.port)

        self.start()

    def js_callback(self, v):
        self.js_result = v

    def run(self):
        # wait for the heartbeat message and add the plane to the map

        while True:
            msg = self.mav.recv_msg()
            self.message_recieved += 1
            msg_type = msg.get_type()
            # print(self.message_recieved, msg_type)
            if msg_type == "HEARTBEAT":
                if not self.marker_create:
                    self.marker_create = True
                    self.uav_lat = self.linkMgr.home_lat
                    self.uav_lng = self.linkMgr.home_lng
                    self.app.sc_map.createMarker(self.uav_name, self.uav_lat, self.uav_lng, self.icon)
            elif msg_type == "GPS_RAW":
                pass
            elif msg_type == "GPS_RAW_INT":
                self.uav_lat = msg.lat/10000000
                self.uav_lng = msg.lon/10000000

                # set home with first GPS get
                if not self.linkMgr.home_create:
                    self.linkMgr.set_home(self.uav_lat, self.uav_lng)

                if not self.marker_create:
                    self.marker_create = True
                    self.app.sc_map.createMarker(self.uav_name, self.uav_lat, self.uav_lng, self.icon)

                self.app.sc_map.moveMarker(self.uav_name, self.uav_lat, self.uav_lng, self)
            elif msg_type == "GLOBAL_POSITION_INT":
                pass
            elif msg_type == "BAD_DATA":
                #print(msg.data)
                debug = False
                if debug:
                    print(self.message_recieved, 'bad_msg')
                    if not self.marker_create:
                        self.marker_create = True
                        self.uav_lat = self.linkMgr.home_lat
                        self.uav_lng = self.linkMgr.home_lng
                        self.app.sc_map.createMarker(self.uav_name, self.uav_lat, self.uav_lng, self.icon)
                    else:
                        self.uav_lat += 0.00001
                        self.uav_lng += 0.00001
                        self.app.sc_map.moveMarker(self.uav_name, self.uav_lat, self.uav_lng)
            else:
                print(msg)


if __name__ == '__main__':
    LI = LinkInterface('10.168.103.72:53')
    print(LI.mav.recv(10))


