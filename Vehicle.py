from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QTimer
from PyQt5.QtPositioning import QGeoCoordinate
from parse.dialects.v10.ardupilotmega import MAVLink_message, MAVLink_heartbeat_message, MAVLink_home_position_message,\
    MAVLink_sys_status_message, MAVLink_autopilot_version_message, MAVLink_vfr_hud_message, MAVLink_attitude_message
from parse.mavutil import mavfile
from LinkInterface import LinkInterface
from MissionManager.MissionManager import MissionManager


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
        self._missionManager = None

        self._firmwarePlugin = None
        self._supportsMissionItemInt = False
        self._offlineEditingVehicle = False
        self.vehicle_name = vehicle_name

        self._sendMessageMultipleList = []          # List of messages being sent multiple times
        self._sendMessageMultipleRetries = 5
        self._sendMessageMultipleIntraMessageDelay = 500

        self._mavCommandQueue = []
        self._mavCommandAckTimer = QTimer()
        self._mavCommandRetryCount = 0
        self._mavCommandMaxRetryCount = 3
        self._mavCommandAckTimeoutMSecs = 3000

        self._sendMultipleTimer = QTimer()
        self._nextSendMessageMultipleIndex = 0

        self._homePosition = None
        self._armed = None
        self._base_mode = 0
        self._custom_mode = 0
        # GPS
        self.lat = None
        self.lng = None
        self.alt = None
        # battery
        self._current_battery = None
        self._voltage_battery = None
        self._battery_remaining = None
        # sensors
        self._onboardControlSensorsPresent = None
        self._onboardControlSensorsEnabled = None
        self._onboardControlSensorsHealth = None
        #
        self._airSpeed = None
        self._groundSpeed = None
        self._climbRate = None
        #  attitude
        self._roll = None
        self._pitch = None
        self._heading = None

        self._flying = False
        self._landing = False

        self._link.messageReceived.connect(self._mavlinkMessageReceived)

        self._commonInit()

        self._firmwarePlugin.initializeVehicle(self)

        # Send MAV_CMD ack timer
        self._mavCommandAckTimer.setSingleShot(True)
        self._mavCommandAckTimer.setInterval(self._mavCommandAckTimeoutMSecs)
        self._mavCommandAckTimer.timeout.connect(self._sendMavCommandAgain)

        self._sendMultipleTimer.start(self._sendMessageMultipleIntraMessageDelay)
        self._sendMultipleTimer.timeout.connect(self._sendMessageMultipleNext)

    def _commonInit(self):
        self._firmwarePlugin = self._firmwarePluginManager.firmwarePluginForAutopilot(self._firmwareType,
                                                                                      self._vehicleType)
        self.positionChanged.connect(self._app.sc_map.bridge.positionChanged)
        # MisssionManager
        self._missionManager = MissionManager(self)

    def __del__(self):
        # qCDebug(VehicleLog) << "~Vehicle" << this;
        del self._missionManager
        self._missionManager = None

    mavlinkMessageReceived = pyqtSignal(object)
    _homePositionChanged = pyqtSignal(object)
    armedChanged = pyqtSignal(int)
    flightModeChanged = pyqtSignal(str)

    positionChanged = pyqtSignal(str, float, float)
    altChanged = pyqtSignal(float)
    battery_remaining_Changed = pyqtSignal(int)
    attitudeChanged = pyqtSignal(float, float, float)

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

        def _handle_SYS_STATUS():
            sysStatus = msg                                                 # type: MAVLink_sys_status_message

            # battery
            if sysStatus.current_battery == -1:
                self._current_battery = None
            else:
                # Current is in Amps, current_battery is 10 * milliamperes (1 = 10 milliampere)
                self._current_battery = sysStatus.current_battery / 100

            if sysStatus.voltage_battery == 0xffff:
                self._voltage_battery = None
            else:
                self._voltage_battery = sysStatus.voltage_battery / 1000

            if sysStatus.battery_remaining == -1:
                self._battery_remaining = None
            elif 0 <= sysStatus.battery_remaining <= 100:
                self._battery_remaining = sysStatus.battery_remaining
                self.battery_remaining_Changed.emit(self._battery_remaining)
            else:
                print('ERROR: battery remaining error %d' % sysStatus.battery_remaining)

            # sensors
                self._onboardControlSensorsPresent = sysStatus.onboard_control_sensors_present
                self._onboardControlSensorsEnabled = sysStatus.onboard_control_sensors_enabled
                self._onboardControlSensorsHealth = sysStatus.onboard_control_sensors_health

        def _handle_GPS_RAW_INT():
            self.lat = msg.lat / 10000000
            self.lng = msg.lon / 10000000
            self.alt = msg.alt / 1000

            self.positionChanged.emit(self.vehicle_name, self.lat, self.lng)
            self.altChanged.emit(self.alt)

        def _handle_ATTITUDE():
            attitude = msg                                                  # type: MAVLink_attitude_message
            pi = 3.14159265358979323846

            self._roll = attitude.roll * (180 / pi)
            self._pitch = attitude.pitch * (180 / pi)
            yaw = attitude.yaw * (180 / pi)
            if yaw < 0:
                yaw += 360
            self._heading = yaw
            self.attitudeChanged.emit(self._pitch, self._roll, self._heading)


        def _handle_VFR_HUD():
            vfrHud = msg                                                    # type: MAVLink_vfr_hud_message
            self._airSpeed = vfrHud.airspeed
            self._groundSpeed = vfrHud.groundspeed
            self._climbRate = vfrHud.climb
            self._heading = vfrHud.heading

        def _handle_AUTOPILOT_VERSION():
            autopilotVersion = msg                                          # type: MAVLink_autopilot_version_message
            # _startPlanRequest

        def _handle_Home_Position():
            homePos = msg                                                   # type: MAVLink_home_position_message
            newHomePosition = QGeoCoordinate(homePos.latitude / 10000000,
                                             homePos.longitude / 10000000,
                                             homePos.altitude / 1000)
            self._setHomePosition(newHomePosition)

        def _handleDefault():
            pass

        switcher = {
            'HEARTBEAT':            _handle_Heardbeat,                      # #0
            'SYS_STATUS':           _handle_SYS_STATUS,                     # #1
            'GPS_RAW_INT':          _handle_GPS_RAW_INT,                    # #24
            'ATTITUDE':             _handle_ATTITUDE,                       # #30
            'VFR_HUD':              _handle_VFR_HUD,                        # #74
            'AUTOPILOT_VERSION':    _handle_AUTOPILOT_VERSION,              # #148
            'HOME_POSITION':        _handle_Home_Position,                  # #242
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

    def flying(self):
        return self._flying

    def _setFlying(self, flying):
        if self._flying != flying:
            self._flying = flying
            # emit flyingChanged(flying);

    def landing(self):
        return self._landing

    def _setLanding(self, landing):
        if self.armd() and self._landing != landing:
            self._landing = landing
            # emit landingChanged(landing)

# get member parameter
    def missionFlightMode(self):
        return 1

    def supportsMissionItemInt(self):
        return self._supportsMissionItemInt

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

# managers
    def missionManager(self):
        return self._missionManager

# armed and flight mode
    def armd(self):
        return self._armed

    def setArmed(self, armed):
        # We specifically use COMMAND_LONG:MAV_CMD_COMPONENT_ARM_DISARM since it is supported by more flight stacks.
        self.sendMavCommand(self._defaultComponentId,
                            400,                        # MAV_CMD_COMPONENT_ARM_DISARM
                            True,                       # show error if fails
                            1 if armed else 0)

    def flightModeSetAvailable(self):
        return self._firmwarePlugin.isCapable(self, 1 << 0)     # SetFlightModeCapability

    def flightModes(self):
        return self._firmwarePlugin.flightModes(self)

    def flightMode(self):
        return self._firmwarePlugin.flightMode(self._base_mode, self._custom_mode)

    def setFlightMode(self, flightMode):
        base_mode = 0
        custom_mode = 0
        # qDebug() << flightMode;
        b, base_mode, custom_mode = self._firmwarePlugin.setFlightMode(flightMode, base_mode, custom_mode)
        if b:
            # setFlightMode will only set MAV_MODE_FLAG_CUSTOM_MODE_ENABLED in base_mode, we need to move back in the
            #  existing states.
            newBaseMode = self._base_mode & ~1       # MAV_MODE_FLAG_DECODE_POSITION_CUSTOM_MODE    1
            newBaseMode |= base_mode
            self._mav.mav.set_mode_send(
                self.id(),                  # target_system
                newBaseMode,                # base_mode
                custom_mode                 # custom_mode
            )
        else:
            # qWarning() << "FirmwarePlugin::setFlightMode failed, flightMode:" << flightMode;
            pass


# send message
    def sendHeartbeat(self):
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

    def sendMavCommand(self, component, command, showError, param1=0, param2=0, param3=0, param4=0, param5=0, param6=0,
                        param7=0):
        entry = {
            'component': component,
            'command': command,
            'showError': showError,
            'param1': param1,
            'param2': param2,
            'param3': param3,
            'param4': param4,
            'param5': param5,
            'param6': param6,
            'param7': param7,
        }
        self._mavCommandQueue.append(entry)
        if len(self._mavCommandQueue) == 1:
            self._mavCommandRetryCount = 0
            self._sendMavCommandAgain()

    def _sendMavCommandAgain(self):
        if not len(self._mavCommandQueue):
            # qWarning() << "Command resend with no commands in queue";
            self._mavCommandAckTimer.stop()
            return

        queuedCommand = self._mavCommandQueue[0]
        if self._mavCommandRetryCount > self._mavCommandMaxRetryCount:
            if queuedCommand['command'] == 520:             # MAV_CMD_REQUEST_AUTOPILOT_CAPABILITIES
                # We aren't going to get a response back for capabilities, so stop waiting for it before we ask for
                #       mission items
                # _setCapabilities(0)
                # _startPlanRequest()
                pass
            # emit mavCommandResult(_id, queuedCommand.component, queuedCommand.command, MAV_RESULT_FAILED,
                # true /* noResponsefromVehicle */);
            self._mavCommandQueue.pop(0)
            self._sendNextQueuedMavCommand()
            return
        self._mavCommandRetryCount += 1

        if self._mavCommandRetryCount > 1:
            # We always let AUTOPILOT_CAPABILITIES go through multiple times even if we don't get acks. This is because
            # we really need to get capabilities and version info back over a lossy link.
            if queuedCommand['command'] != 520:             # MAV_CMD_REQUEST_AUTOPILOT_CAPABILITIES
                if self.px4Firmware():
                    pass
                else:
                    if queuedCommand['command'] != 500:     #MAV_CMD_START_RX_PAIR
                        # The implementation of this command comes from the IO layer and is shared across stacks. So
                        # for other firmwares we aren't really sure whether they are correct or not.
                        return
            # qCDebug(VehicleLog) << "Vehicle::_sendMavCommandAgain retrying command:_mavCommandRetryCount" <<
                        # queuedCommand.command << _mavCommandRetryCount;
        self._mavCommandAckTimer.start()

        self._mav.mav.command_long_send(
            self.id(),                          # target_system
            self._defaultComponentId,           # target_component
            queuedCommand['command'],           # command
            0,                                  # confirmation
            queuedCommand['param1'],            # param1
            queuedCommand['param2'],            # param2
            queuedCommand['param3'],            # param3
            queuedCommand['param4'],            # param4
            queuedCommand['param5'],            # param5
            queuedCommand['param6'],            # param6
            queuedCommand['param7']             # param7
        )

    def _sendNextQueuedMavCommand(self):
        if len(self._mavCommandQueue):
            self._mavCommandRetryCount = 0
            self._sendMavCommandAgain()
