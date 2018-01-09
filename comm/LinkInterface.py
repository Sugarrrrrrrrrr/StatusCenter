import threading
from parse import mavutil


class LinkInterface(threading.Thread):
    def __init__(self, uav, app, linkMgr):
        super().__init__()
        self.app = app
        self.uav = uav
        self.linkMgr = linkMgr

        self.marker_create = False
        self.uav_lat = None
        self.uav_lng = None
        self.message_recieved = 0

        self.js_result = None

    # connect mode choose
        self.connect_type = uav['type']
        if self.connect_type == 0:
            self.uav_name = uav['name']
            self.ip = uav['ip']
            self.port = uav['port']
            self.icon = uav['icon']
            self.network = '.'.join(self.ip.split('.')[:-1]) + '.0'
            self.mav = mavutil.mavlink_connection('network:' + self.network, ip_list=[self.ip], port=self.port)
        elif self.connect_type == 1:
            self.uav_name = uav['name']
            self.ip = uav['ip']
            self.port = uav['port']
            self.icon = uav['icon']
            self.mav = mavutil.mavlink_connection('udp:' + self.ip + ':' + str(self.port))
        else:
            print('error: unknow connect_type: ', self.connect_type)
            return
    # -----

    # Vehicle class attributes
    #    self._firmwareType = 3         # MAV_AUTOPILOT_ARDUPILOTMEGA       3
    #    self._supportsMissionItemInt = False
    # -----

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
                # print(msg.data)
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

    # Vehicle class methods
    '''
    def id(self):
        return 1

    def defaultComponentId(self):
        return 1

    def apmFirmware(self):
        return self._firmwareType == 3      # MAV_AUTOPILOT_ARDUPILOTMEGA       3

    def px4Firmware(self):
        return self._firmwareType == 12     # MAV_AUTOPILOT_PX4                 12

    def genericFirmware(self):
        return not self.apmFirmware() and not self.px4Firmware()

    def setHomePosition(self, x, y, z):
        pass

    def sendHomePositionToVehicle(self) -> bool:    # method of class FirmwarePlugin
        if self.__firmwareType == 3:
            # APM stack wants the home position sent in the first position
            return True
        elif self.__firmwareType == 12:
            # PX4 stack does not want home position sent in the first position.
            # Subsequent sequence numbers must be adjusted.
            return False
        else:
            # Generic stack does not want home position sent in the first position.
            # Subsequent sequence numbers must be adjusted.
            # This is the mavlink spec default.
            return False

    def flightMode(self):
        return 1

    def missionFlightMode(self):
        return 1

    def supportsMissionItemInt(self):
        return self._supportsMissionItemInt
    '''
    # -----


if __name__ == '__main__':
    LI = LinkInterface('10.168.103.72:53')
    print(LI.mav.recv(10))
