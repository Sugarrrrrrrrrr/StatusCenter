from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QTimer
from PyQt5.QtPositioning import QGeoCoordinate
from parse.dialects.v10.ardupilotmega import MAVLink_message, MAVLink_heartbeat_message, MAVLink_home_position_message
from parse.mavutil import mavfile
from LinkInterface import LinkInterface


class Vehicle(QObject):
    def __init__(self, app, link, vehicleId, defaultComponentId, firmwareType, vehicleType, firmwarePluginManager,
                 vehicle_name=None, parent=None):
        super().__init__(parent=parent)
        self._app = app
        self._link = link                           # type: LinkInterface
        self._mav = link.mav                        # type: mavfile

        self._id = vehicleId
        self._defaultComponentId = defaultComponentId
        self._firmwareType = firmwareType                       # MAV_AUTOPILOT_ARDUPILOTMEGA       3
        self._vehicleType = vehicleType
        self._firmwarePluginManager = firmwarePluginManager     # type: FirmwarePluginManager

        self._firmwarePlugin = None
        self._supportsMissionItemInt = False
        self._offlineEditingVehicle = False
        self.vehicle_name = vehicle_name

        self._sendMessageMultipleList = []          # List of messages being sent multiple times
        self._sendMessageMultipleRetries = 5
        self._sendMessageMultipleIntraMessageDelay = 500

        self._sendMultipleTimer = QTimer()
        self._nextSendMessageMultipleIndex = 0

        self._homePosition = None
        self._armed = None
        self._base_mode = 0
        self._custom_mode = 0

        self._link.messageReceived.connect(self._mavlinkMessageReceived)

        self._commonInit()

        self._firmwarePlugin.initializeVehicle(self)

        self._sendMultipleTimer.start(self._sendMessageMultipleIntraMessageDelay)
        self._sendMultipleTimer.timeout.connect(self._sendMessageMultipleNext)

    def _commonInit(self):
        self._firmwarePlugin = self._firmwarePluginManager.firmwarePluginForAutopilot(self._firmwareType,
                                                                                      self._vehicleType)

        self.positionChanged.connect(self._app.sc_map.bridge.positionChanged)
        # MisssionManager
        pass

    def __del__(self):
        pass

    mavlinkMessageReceived = pyqtSignal(object)
    _homePositionChanged = pyqtSignal(object)
    armedChanged = pyqtSignal(int)
    flightModeChanged = pyqtSignal(object)

    positionChanged = pyqtSignal(str, float, float)

    @pyqtSlot(object)
    def _mavlinkMessageReceived(self, msg: MAVLink_message):
        msgType = msg.get_type()

        def _handle_Heardbeat():
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

        def _handle_Home_Position():
            homePos = msg                                                   # type: MAVLink_home_position_message
            newHomePosition = QGeoCoordinate(homePos.latitude / 10000000,
                                             homePos.longitude / 10000000,
                                             homePos.altitude / 1000)
            self._setHomePosition(newHomePosition)

        def _handle_GPS_RAW_INT():
            self.lat = msg.lat / 10000000
            self.lng = msg.lon / 10000000

            self.positionChanged.emit(self.vehicle_name, self.lat, self.lng)

        def _handleDefault():
            pass

        switcher = {
            'HEARTBEAT': _handle_Heardbeat,
            'HOME_POSITION': _handle_Home_Position,
            'GPS_RAW_INT': _handle_GPS_RAW_INT,
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

    # Property accesors
    def id(self):
        return self._id

    def firmwareType(self):
        return self._firmwareType

    def vehicleType(self):
        return self._vehicleType

    def vehicleTypeName(self):
        pass

    def defaultComponentId(self):
        return self._defaultComponentId

    # Provides access to the Firmware Plugin for this Vehicle
    def firmwarePlugin(self):
        return self._firmwarePlugin

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

    def isOfflineEditingVehicle(self):
        return self._offlineEditingVehicle

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

    def requestDataStream(self, stream, rate, sendMultiple=True):       # MAV_DATA_STREAM stream
        msg = self._mav.mav.request_data_stream_encode(
            self.id(),                  # target_system
            self._defaultComponentId,   # target_component
            stream,                     # req_stream_id
            rate,                       # req_message_rate
            1                           # start_stop                : 1 to start sending, 0 to stop sending. (uint8_t)
        )
        if sendMultiple:
            # We use sendMessageMultiple since we really want these to make it to the vehicle
            self.sendMessageMultiple(msg)
        else:
            self._mav.mav.send(msg)

    def sendMessageMultiple(self, msg):
        info = (msg, self._sendMessageMultipleRetries)
        self._sendMessageMultipleList.append(info)

    def _sendMessageMultipleNext(self):
        if self._nextSendMessageMultipleIndex < len(self._sendMessageMultipleList):
            # qCDebug(VehicleLog) << "_sendMessageMultipleNext:"
            #       << _sendMessageMultipleList[_nextSendMessageMultipleIndex].message.msgid;
            self._mav.mav.send(self._sendMessageMultipleList[self._nextSendMessageMultipleIndex][0])

            if self._sendMessageMultipleList[self._nextSendMessageMultipleIndex][1] - 1 < 0:
                self._sendMessageMultipleList.pop(self._nextSendMessageMultipleIndex)
            else:
                info = self._sendMessageMultipleList[self._nextSendMessageMultipleIndex]
                self._sendMessageMultipleList[self._nextSendMessageMultipleIndex] = (info[0], info[1] - 1)
                self._nextSendMessageMultipleIndex += 1

            if self._nextSendMessageMultipleIndex >= len(self._sendMessageMultipleList):
                self._nextSendMessageMultipleIndex = 0