from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
from PyQt5.QtPositioning import QGeoCoordinate
from parse.dialects.v10.ardupilotmega import MAVLink_message, MAVLink_heartbeat_message, MAVLink_home_position_message
from parse.mavutil import mavfile
from LinkInterface import LinkInterface

class Vehicle(QObject):
    def __init__(self, app, link, vehicleId=1, defaultComponentId=1, vehicle_name=None, parent=None):
        super().__init__(parent=parent)
        self._app = app
        self._link = link                           # type: LinkInterface
        self._mav = link.mav                        # type: mavfile

        self._firmwareType = 3                      # MAV_AUTOPILOT_ARDUPILOTMEGA       3
        self._supportsMissionItemInt = False
        self._id = vehicleId
        self._defaultComponentId = defaultComponentId
        self.vehicle_name = vehicle_name

        self._homePosition = None
        self._armed = None
        self._base_mode = 0
        self._custom_mode = 0

        self._link.messageReceived.connect(self._mavlinkMessageReceived)
        print(self.vehicle_name)

    def __del__(self):
        pass

    mavlinkMessageReceived = pyqtSignal(object)
    _homePositionChanged = pyqtSignal(object)
    armedChanged = pyqtSignal(int)
    flightModeChanged = pyqtSignal(object)

    @pyqtSlot(object)
    def _mavlinkMessageReceived(self, msg: MAVLink_message):
        msgType = msg.get_type()

        def _handleHeardbeat():
            if msg.get_srcComponent() != self._defaultComponentId:
                print('error: Vehicle._handleHeardbeat compid error')
                return

            heartbeat = msg                                                 # type: MAVLink_heartbeat_message

            newArmed = heartbeat.base_mode & 128    # MAV_MODE_FLAG_DECODE_POSITION_SAFETY      128
            if self._armed != newArmed:
                self._armed = newArmed
                self.armedChanged.emit(self._armed)

                # We are transitioning to the armed state, begin tracking trajectory points for the map
                if self._armed:
                    # _mapTrajectoryStart()
                    pass
                else:
                    # _mapTrajectoryStop()
                    pass

            if heartbeat.base_mode != self._base_mode or heartbeat.custom_mode != self._custom_mode:
                previousFlightMode = None
                if self._custom_mode != 0 or self._custom_mode != 0:
                    # Vehicle is initialized with _base_mode=0 and _custom_mode=0. Don't pass this to flightMode()
                    #   since it will complain about bad modes while unit testing.
                    previousFlightMode = self.flightMode()
                self._base_mode = heartbeat.base_mode
                self._custom_mode = heartbeat.custom_mode
                if previousFlightMode != self.flightMode():
                    self.flightModeChanged.emit(self.flightMode())

        def _handleHomePosition():
            homePos = msg                                                   # type: MAVLink_home_position_message
            newHomePosition = QGeoCoordinate(homePos.latitude / 10000000,
                                             homePos.longitude / 10000000,
                                             homePos.altitude / 1000)
            self._setHomePosition(newHomePosition)

        def _handleDefault():
            pass

        switcher = {
            'HEARTBEAT': _handleHeardbeat,
            'HOME_POSITION': _handleHomePosition,
        }
        switcher.get(msgType, _handleDefault)()

        self.mavlinkMessageReceived.emit(msg)

    def _setHomePosition(self, homeCoord):
        if homeCoord != self._homePosition:
            self._homePosition = homeCoord
            self._homePositionChanged.emit(self._homePosition)

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

# get member parameter
    def flightMode(self):
        return 1

    def missionFlightMode(self):
        return 1

    def supportsMissionItemInt(self):
        return self._supportsMissionItemInt

    def flightMode(self):
        return self._base_mode, self._custom_mode

    def apmFirmware(self):
        return self._firmwareType == 3              # MAV_AUTOPILOT_ARDUPILOTMEGA       3

    def px4Firmware(self):
        return self._firmwareType == 12             # MAV_AUTOPILOT_PX4                 12

    def genericFirmware(self):
        return not self.apmFirmware() and not self.px4Firmware()

    def id(self):
        return self._id

    def defaultComponentId(self):
        return self._defaultComponentId

    def getMav(self):
        return self._mav

    def getLink(self):
        return self._link

# send message
    def sendHearbet(self):
        self._mav.mav.heartbeat_send(
            6,              # type              MAV_TYPE_GCS                6
            8,              # autopilot         MAV_AUTOPILOT_INVALID       8
            192,            # base_mode         MAV_MODE_MANUAL_ARMED     192
            0,              # custom_mode
            4               # system_status     MAV_STATE_ACTIVE            4
        )
