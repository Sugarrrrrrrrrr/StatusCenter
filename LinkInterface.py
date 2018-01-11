from parse import mavutil
from PyQt5.QtCore import QThread, pyqtSignal

from parse.dialects.v10.ardupilotmega import MAVLink_heartbeat_message


class LinkInterface(QThread):
    def __init__(self, uav, app, linkMgr):
        super().__init__()
        self.app = app
        self.uav = uav
        self.linkMgr = linkMgr
        self._vehicle = None

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
            # type: mavutil.mavfile
        elif self.connect_type == 1:
            self.uav_name = uav['name']
            self.ip = uav['ip']
            self.port = uav['port']
            self.icon = uav['icon']
            self.mav = mavutil.mavlink_connection('udp:' + self.ip + ':' + str(self.port))      # type: mavutil.mavfile
        else:
            print('error: unknow connect_type: ', self.connect_type)
            return
    # -----

    # Vehicle class attributes
    #    self._firmwareType = 3         # MAV_AUTOPILOT_ARDUPILOTMEGA       3
    #    self._supportsMissionItemInt = False
    # -----
        self.start()

# signals
    messageReceived = pyqtSignal(object)    # msg
    vehicleHeartbeatInfo = pyqtSignal(object, int, int, int, int, int)
    # link, vehicleId, componentId, vehicleMavlinkVersion, vehicleFirmwareType, vehicleType

    def js_callback(self, v):
        self.js_result = v

    def run(self):
        # wait for the heartbeat message
        # if self.connect_type == 0:
        #     msg = None
        #     self._vehicle = Vehicle(self.app, self)
        # elif self.connect_type == 1:
        #     msg = self.mav.wait_heartbeat()
        #     self._vehicle = Vehicle(self.app, self)
        # else:
        #     print('error: unknow connect_type: ', self.connect_type)
        #     return
        # self._handleMsg(msg)

        #  add the plane to the map

        #
        while True:
            msg = self.mav.recv_msg()
            self.message_recieved += 1

            # # # # #
            self._handleMsg(msg)
            self.messageReceived.emit(msg)

    def _handleMsg(self, msg: MAVLink_heartbeat_message):
        if not msg:
            return

        msg_type = msg.get_type()
        if msg_type == "HEARTBEAT":
            self.vehicleHeartbeatInfo.emit(self, msg.get_srcSystem(), msg.get_srcComponent(), msg.mavlink_version,
                                           msg.autopilot, msg.type)
# old ------------------------------------------------------------------------------------------------------------------
            if not self.marker_create:
                self.marker_create = True
                self.uav_lat = self.linkMgr.home_lat
                self.uav_lng = self.linkMgr.home_lng
                self.app.sc_map.createMarker(self.uav_name, self.uav_lat, self.uav_lng, self.icon)

        elif msg_type == "GPS_RAW_INT":
            self.uav_lat = msg.lat / 10000000
            self.uav_lng = msg.lon / 10000000

            # set home with first GPS get
            if not self.linkMgr.home_create:
                self.linkMgr.set_home(self.uav_lat, self.uav_lng)

            if not self.marker_create:
                self.marker_create = True
                self.app.sc_map.createMarker(self.uav_name, self.uav_lat, self.uav_lng, self.icon)

            self.app.sc_map.moveMarker(self.uav_name, self.uav_lat, self.uav_lng, self)

        else:
            print(msg)
# ----------------------------------------------------------------------------------------------------------------------


if __name__ == '__main__':
    LI = LinkInterface('10.168.103.72:53')
    print(LI.mav.recv(10))
