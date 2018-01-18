from PyQt5.QtCore import QObject, QThread, QEventLoop
from PyQt5.QtPositioning import QGeoCoordinate
from PyQt5.QtWidgets import QApplication

from typing import List

from Vehicle import Vehicle

_instance = None


class FirmwarePlugin(QObject):
    # @return The AutoPilotPlugin associated with this firmware plugin. Must be overridden.
    def autopilotPlugin(self, vehicle):
        pass

    # Called when Vehicle is first created to perform any firmware specific setup.
    def initializeVehicle(self, vehicle: Vehicle):
        # Generic Flight Stack is by definition "generic", so no extra work
        pass

    # @return true: Firmware supports all specified capabilites
    def isCapable(self, vehicle, capabilities):
        pass

    # Returns VehicleComponents for specified Vehicle
    #   @param vehicle Vehicle  to associate with components
    # @return List of VehicleComponents for the specified vehicle. Caller owns returned objects and must free when no
    #   longer needed.
    def componentsForVehicle(self, vehicle):        # AutoPilotPlugin* vehicle -> QList<VehicleComponent*>
        pass

    # Returns the list of available flight modes
    def flightModes(self, vehicle):
        pass

    # Returns the name for this flight mode. Flight mode names must be human readable as well as audio speakable.
    #   @param base_mode Base mode from mavlink HEARTBEAT message
    #   @param custom_mode Custom mode from mavlink HEARTBEAT message
    def flightMode(self, base_mode, custom_mode):
        pass

    # Sets base_mode and custom_mode to specified flight mode.
    #   @param[out] base_mode Base mode for SET_MODE mavlink message
    #   @param[out] custom_mode Custom mode for SET_MODE mavlink message
    def setFlightMode(self, flightMode, base_mode, custom_mode):
        # qWarning() << "FirmwarePlugin::setFlightMode called on base class, not supported"
        return False, base_mode, custom_mode

    # Returns The flight mode which indicates the vehicle is paused
    def pauseFlightMode(self):
        return ''

    # Returns the flight mode for running missions
    def missionFlightMode(self):
        return ''

    # Returns the flight mode for RTL
    def rtlFlightMode(self):
        return

    # Returns the flight mode for Land
    def landFlightMode(self):
        return ''

    # Returns the flight mode to use when the operator wants to take back control from autonomouse flight.
    def takeControlFlightMode(self):
        return ''

    # Returns whether the vehicle is in guided mode or not
    def isGuidedMode(self, vehicle):
        # Not supported by generic vehicle
        return False

    # Set guided flight mode
    def setGuidedMode(self, vehicle, guidedMode):
        # qgcApp()->showMessage(guided_mode_not_supported_by_vehicle);
        pass

    # Causes the vehicle to stop at current position. If guide mode is supported, vehicle will be let in guide mode.
    # If not, vehicle will be left in Loiter.
    def pauseVehicle(self, vehicle):
        # Not supported by generic vehicle
        pass

    # Command vehicle to return to launch
    def guidedModeRTL(self, vehicle):
        # Not supported by generic vehicle
        pass

    # Command vehicle to land at current location
    def guidedModeLand(self, vehicle):
        # Not supported by generic vehicle
        pass

    # Command vehicle to takeoff from current location to a firmware specific height.
    def guidedModeTakeoff(self, vehicle):
        # Not supported by generic vehicle
        pass

    # Command the vehicle to start the mission
    def startMission(self, vehicle):
        # Not supported by generic vehicle
        pass

    # Command vehicle to orbit given center point
    #   @param centerCoord Center Coordinates
    def guidedModeOrbit(self, vehicle, centerCoord, radius, velocity, altitude):
        # Not supported by generic vehicle
        pass

    # Command vehicle to move to specified location (altitude is included and relative)
    def guidedModeGotoLocation(self, vehicle, gotoCoord):
        # Not supported by generic vehicle
        pass

    # Command vehicle to change altitude
    #   @param altitudeChange If > 0, go up by amount specified, if < 0, go down by amount specified
    def guidedModeChangeAltitude(self, vehicle, altitudeChange):
        # Not supported by generic vehicle
        pass

    # FIXME: This isn't quite correct being here. All code for Joystick suvehicleTypepport is currently firmware
    #       specific not just this. I'm going to try to change that. If not, this will need to be removed.
    # Returns the number of buttons which are reserved for firmware use in the MANUAL_CONTROL mavlink message. For
    #       example PX4 Flight Stack reserves the first 8 buttons to simulate rc switches.
    # The remainder can be assigned to Vehicle actions.
    # @return -1: reserver all buttons, >0 number of buttons to reserve
    def manualControlReservedButtonCount(self):
        # We don't know whether the firmware is going to used any of these buttons.
        # So reserve them all.
        return -1

    # Default tx mode to apply to joystick axes
    # TX modes are as outlined here: http://www.rc-airplane-world.com/rc-transmitter-modes.html
    def defaultJoystickTXMode(self):
        return 2

    # Returns true if the vehicle and firmware supports the use of a throttle joystick that is zero when centered.
    #       Typically not supported on vehicles that have bidirectional throttle.
    def supportsThrottleModeCenterZero(self):
        # By default, this is supported
        return True

    # Returns true if the firmware supports the use of the MAVlink "MANUAL_CONTROL" message.
    # By default, this returns false unless overridden in the firmware plugin.
    def supportsManualControl(self):
        return False

    # Returns true if the firmware supports the use of the RC radio and requires the RC radio setup page. Returns
    #       true by default.
    def supportsRadio(self):
        return True

    # Returns true if the firmware supports the AP_JSButton library, which allows joystick buttons to be assigned via
    #       parameters in firmware. Default is false.
    def supportsJSButton(self):
        return False

    # Returns true if the firmware supports calibrating motor interference offsets for the compass (CompassMot).
    #       Default is true.
    def supportsMotorInterference(self):
        return True

    # Called before any mavlink message is processed by Vehicle such that the firmwre plugin can adjust any message
    # characteristics. This is handy to adjust or differences in mavlink spec implementations such that the base code
    # can remain mavlink generic.
    #   @param vehicle Vehicle message came from
    #   @param message[in,out] Mavlink message to adjust if needed.
    # @return false: skip message, true: process message
    def adjustIncomingMavlinkMessage(self, vehicle, message):
        # Generic plugin does no message adjustment
        return True

    # Called before any mavlink message is sent to the Vehicle so plugin can adjust any message characteristics. This
    # is handy to adjust or differences in mavlink spec implementations such that the base code can remain mavlink
    # generic.
    #   @param vehicle Vehicle message came from
    #   @param outgoingLink Link that messae is going out on
    #   @param message[in,out] Mavlink message to adjust if needed.
    def adjustOutgoingMavlinkMessage(self, vehicle, outgoingLink, message):
        # Generic plugin does no message adjustment
        pass

    # Determines how to handle the first item of the mission item list. Internally to QGC the first item is always
    # the home position.
    # @return
    #   true: Send first mission item as home position to vehicle. When vehicle has no mission items on it, it may or
    #           may not return a home position back in position 0.
    #   false: Do not send first item to vehicle, sequence numbers must be adjusted
    def sendHomePositionToVehicle(self):
        # Generic stack does not want home position sent in the first position.
        # Subsequent sequence numbers must be adjusted.
        # This is the mavlink spec default.
        return False

    # Returns the parameter which is used to identify the version number of parameter set
    def getVersionParam(self):
        return ''

    # Returns the parameter set version info pulled from inside the meta data file. -1 if not found.
    #   @param metaDataFile unused
    #   @param majorVersion[out]
    #   @param minorVersion[out]
    # @return majorVersion,minorVersion
    def getParameterMetaDataVersionInfo(self, metaDataFile, majorVersion, minorVersion):
        majorVersion = -1
        minorVersion = -1
        return majorVersion, minorVersion

    # Returns the internal resource parameter meta date file.
    def internalParameterMetaDataFile(self, vehicle):
        return ''

    # Loads the specified parameter meta data file.
    # @return Opaque parameter meta data information which must be stored with Vehicle. Vehicle is responsible to call
    #           deleteParameterMetaData when no longer needed.
    def loadParameterMetaData(self, metaDataFile):
        return None

    # Adds the parameter meta data to the Fact
    #   @param opaqueParameterMetaData Opaque pointer returned from loadParameterMetaData
    def addMetaDataToFact(self, parameterMetaData, fact, vehicleType):
        return

    # List of supported mission commands. Empty list for all commands supported.
    def supportedMissionCommands(self):
        # Generic supports all commands
        return []

    # Returns the name of the mission command json override file for the specified vehicle type.
    #   @param vehicleType Vehicle type to return file for, MAV_TYPE_GENERIC is a request for overrides for all vehicle
    #       types
    def missionCommandOverrides(self, vehicleType):
        switcher = {
            0: ':/json/MavCmdInfoCommon.json',
            1: ':/json/MavCmdInfoFixedWing.json',
            2: ':/json/MavCmdInfoMultiRotor.json',
            20: ':/json/MavCmdInfoVTOL.json',
            12: ':/json/MavCmdInfoSub.json',
            10: ':/json/MavCmdInfoRover.json',
        }
        s = switcher.get(vehicleType, None)
        if s:
            return s
        else:
            # qWarning() << "FirmwarePlugin::missionCommandOverrides called with bad MAV_TYPE:" << vehicleType;
            return ''

    # Returns the mapping structure which is used to map from one parameter name to another based on firmware version.
    def paramNameRemapMajorVersionMap(self):
        pass

    # Returns the highest major version number that is known to the remap for this specified major version.
    def remapParamNameHigestMinorVersionNumber(self, majorVersionNumber):
        return 0

    # @return true: Motors are coaxial like an X8 config, false: Quadcopter for example
    def multiRotorCoaxialMotors(self, vehicle):
        return False

    # @return true: X confiuration, false: Plus configuration
    def multiRotorXConfig(self, vehicle):
        return False

    # Returns a newly created geofence manager for this vehicle.
    def newGeoFenceManager(self, vehicle):
        # return new GeoFenceManager(vehicle)
        pass

    # Returns the parameter which holds the fence circle radius if supported.
    def geoFenceRadiusParam(self, vehicle):
        return ''

    # Returns a newly created rally point manager for this vehicle.
    def newRallyPointManager(self, vehicle):
        # return new RallyPointManager(vehicle)
        pass

    # Return the resource file which contains the set of params loaded for offline editing.
    def offlineEditingParamFile(self, vehicle):
        return ''

    # Return the resource file which contains the brand image for the vehicle for Indoor theme.
    def brandImageIndoor(self, vehicle):
        return ''

    # Return the resource file which contains the brand image for the vehicle for Outdoor theme.
    def brandImageOutdoor(self, vehicle):
        return ''

    # Return the resource file which contains the vehicle icon used in the flight view when the view is dark (
    #       Satellite for instance)
    def vehicleImageOpaque(self, vehicle):
        return "/qmlimages/vehicleArrowOpaque.svg"

    # Return the resource file which contains the vehicle icon used in the flight view when the view is light (Map
    #       for instance)
    def vehicleImageOutline(self, vehicle):
        return "/qmlimages/vehicleArrowOutline.svg"

    # Return the resource file which contains the vehicle icon used in the compass
    def vehicleImageCompass(self, vehicle):
        return "/qmlimages/compassInstrumentArrow.svg"

    # Allows the core plugin to override the toolbar indicators
    # @return A list of QUrl with the indicators (see MainToolBarIndicators.qml)
    def toolBarIndicators(self, vehicle):
        pass

    # Returns a list of CameraMetaData objects for available cameras on the vehicle.
    def cameraList(self, vehicle):
        pass

    # Returns a pointer to a dictionary of firmware-specific FactGroups
    def factGroups(self):
        # Generic plugin has no FactGroups
        return None

    # @true: When flying a mission the vehicle is always facing towards the next waypoint
    def vehicleYawsToNextWaypointInMission(self, vehicle):
        # return vehicle->multiRotor() ? false : true;
        pass

    # Returns the data needed to do battery consumption calculations
    #   @param[out] mAhBattery Battery milliamp-hours rating (0 for no battery data available)
    #   @param[out] hoverAmps Current draw in amps during hover
    #   @param[out] cruiseAmps Current draw in amps during cruise
    # @return mAhBattery, hoverAmps, cruiseAmps
    def batteryConsumptionData(self, vehicle, mAhBattery, hoverAmps, cruiseAmps):
        mAhBattery = 0
        hoverAmps = 0
        cruiseAmps = 0
        return mAhBattery, hoverAmps, cruiseAmps

    # Returns the parameter which control auto-disarm. Assume == 0 means no auto disarm
    def autoDisarmParameter(self, vehicle):
        return ''

    # Used to determine whether a vehicle has a gimbal.
    #   @param[out] rollSupported Gimbal supports roll
    #   @param[out] pitchSupported Gimbal supports pitch
    #   @param[out] yawSupported Gimbal supports yaw
    # @return (bool, rollSupported, pitchSupported, yawSupported)
    #       true: vehicle has gimbal, false: gimbal support unknown
    def hasGimbal(self, vehicle, rollSupported, pitchSupported, yawSupported):
        rollSupported = False
        pitchSupported = False
        yawSupported = False
        return False, rollSupported, pitchSupported, yawSupported

    # Arms the vehicle with validation and retries
    # @return: true - vehicle armed, false - vehicle failed to arm
    def _armVehicleAndValidate(self, vehicle):
        if vehicle.armd():
            return True
        armed_changed = False
        q_thread = QThread()
        # try 3 times
        for retry in range(3):
            vehicle.setArmed(True)
            # wait for vehicle to return armed state for 3 seconds
            for i in range(30):
                if vehicle.armd():
                    armed_changed = True
                    break
                q_thread.msleep(100)
                QApplication.processEvents(QEventLoop.ExcludeUserInputEvents)
            if armed_changed:
                break
        return armed_changed

    # Sets the vehicle to the specified flight mode with validation and retries
    # @return: true - vehicle in specified flight mode, false - flight mode change failed
    def _setFlightModeAndValidate(self, vehicle, flight_mode):
        if vehicle.flightMode() == flight_mode:
            return True
        flight_mode_changed = False
        q_thread = QThread()
        # try 3 times
        for retry in range(3):
            vehicle.setFlightMode(flight_mode)
            # wait for vehicle to return flight mode
            for i in range(13):
                if vehicle.flightMode() == flight_mode:
                    flight_mode_changed = True
                    break
                q_thread.msleep(100)
                QApplication.processEvents(QEventLoop.ExcludeUserInputEvents)
            if flight_mode_changed:
                break
        return flight_mode_changed


class APMFirmwareVersion:
    def __init__(self, versionText = ''):
        self._versionString = None
        self._vehicleType = None
        self._major = 0
        self._minor = 0
        self._patch = 0
        self._parseVersion(versionText)

    def isValid(self):
        return self._versionString is not None

    def isBeta(self):
        if self._versionString.find('.rc') != -1:
            return True
        else:
            return False

    def isDev(self):
        if self._versionString.find('.dev') != -1:
            return True
        else:
            return False

    def operator(self, other):
        myVersion = self._major << 16 | self._minor << 8 | self._patch
        otherVersion = other.majorNumber() << 16 | other.minorNumber() << 8 | other.patchNumber()
        return myVersion < otherVersion

    def versionString(self):
        return self._versionString

    def vehicleType(self):
        return self._vehicleType

    def majorNumber(self):
        return self._major

    def minorNumber(self):
        return self._minor

    def patchNumber(self):
        return self._patch

    def _parseVersion(self, versionText):
        pass

class APMCustomMode:
    def __init__(self, mode, settable):
        self._mode = mode
        self._settable = settable
        self._enumToString = None

    def modeAsInt(self):
        return self._mode

    def canBeSet(self):
        return self._settable

    def modeString(self):
        mode = None
        try:
            mode = self._enumToString[self.modeAsInt()]
        except Exception as e:
            pass
        if not mode:
            mode = 'mode' + str(self.modeAsInt())
        return mode

    def setEnumToStringMapping(self, enumToString):
        self._enumToString = enumToString


class APMFirmwarePlugin(FirmwarePlugin):
    # Overrides from FirmwarePlugin
    def componentsForVehicle(self, vehicle):
        return []

    def supportedMissionCommands(self):
        list = [
            16,         # MAV_CMD_NAV_WAYPOINT
            17,         # MAV_CMD_NAV_WAYPOINT
            18,         # MAV_CMD_NAV_LOITER_TURNS
            19,         # MAV_CMD_NAV_LOITER_TIME
            20,         # MAV_CMD_NAV_RETURN_TO_LAUNCH
            21,         # MAV_CMD_NAV_LAND
            22,         # MAV_CMD_NAV_TAKEOFF
            30,         # MAV_CMD_NAV_LOITER_TO_ALT
            82,         # MAV_CMD_NAV_SPLINE_WAYPOINT
            92,         # MAV_CMD_NAV_GUIDED_ENABLE
            93,         # MAV_CMD_NAV_DELAY
            112,        # MAV_CMD_CONDITION_DELAY
            114,        # MAV_CMD_CONDITION_DISTANCE
            115,        # MAV_CMD_CONDITION_YAW
            176,        # MAV_CMD_DO_SET_MODE
            177,        # MAV_CMD_DO_JUMP
            178,        # MAV_CMD_DO_CHANGE_SPEE
            179,        # MAV_CMD_DO_SET_HOME
            181,        # MAV_CMD_DO_SET_RELAY
            182,        # MAV_CMD_DO_REPEAT_RELAY
            183,        # MAV_CMD_DO_SET_SERVO
            184,        # MAV_CMD_DO_REPEAT_SERVO
            189,        # MAV_CMD_DO_LAND_START
            201,        # MAV_CMD_DO_SET_ROI
            202,        # MAV_CMD_DO_DIGICAM_CONFIGURE
            203,        # MAV_CMD_DO_DIGICAM_CONTROL
            205,        # MAV_CMD_DO_MOUNT_CONTROL
            206,        # MAV_CMD_DO_SET_CAM_TRIGG_DIST
            207,        # MAV_CMD_DO_FENCE_ENABLE
            208,        # MAV_CMD_DO_PARACHUTE
            210,        # MAV_CMD_DO_INVERTED_FLIGHT
            211,        # MAV_CMD_DO_GRIPPER
            222,        # MAV_CMD_DO_GUIDED_LIMITS
            212,        # MAV_CMD_DO_AUTOTUNE_ENABLE
            84,         # MAV_CMD_NAV_VTOL_TAKEOFF
            85,         # MAV_CMD_NAV_VTOL_LAND
            3000,       # MAV_CMD_DO_VTOL_TRANSITION
        ]
        return list

    def autopilotPlugin(self, vehicle):
        # return new APMAutoPilotPlugin(vehicle, vehicle);
        pass

    def isCapable(self, vehicle, capabilities):
        return (capabilities & (1 << 0 | 1 << 2)) == capabilities
        # SetFlightModeCapability   1 << 0
        # PauseVehicleCapability    1 << 2

    def flightModes(self, vehicle):
        flightModesList = []
        for customMode in self._supportedModes:
            if customMode.canBeSet():
                flightModesList.append(customMode.modeString())
        return flightModesList

    def flightMode(self, base_mode, custom_mode):
        flightMode = 'Unknown'
        if base_mode & 1:       # MAV_MODE_FLAG_CUSTOM_MODE_ENABLED 1
            for customMode in self._supportedModes:
                if customMode.modeAsInt() == custom_mode:
                    flightMode = customMode.modeString()
        return flightMode

    def setFlightMode(self, flightMode: str, base_mode, custom_mode):
        base_mode = 0
        custom_mode = 0
        found = False
        for mode in self._supportedModes:
            if flightMode.lower() == mode.modeString().lower():
                base_mode = 1
                custom_mode = mode.modeAsInt()
                found = True
                break
        if not found:
            # qCWarning(APMFirmwarePluginLog) << "Unknown flight Mode" << flightMode;
            pass
        return found, base_mode, custom_mode

    def isGuidedMode(self, vehicle):
        return vehicle.flightMode() == 'Guided'

    def pauseVehicle(self, vehicle):
        # Best we can do in this case
        vehicle.setFlightMode('Loiter')

    def manualControlReservedButtonCount(self):
        # We don't know whether the firmware is going to used any of these buttons.
        # So reserve them all.
        return -1

    def adjustIncomingMavlinkMessage(self, vehicle, message):
        # Don't process messages to/from UDP Bridge. It doesn't suffer from these issues
        if message.compid == 240:       # MAV_COMP_ID_UDP_BRIDGE
            return True

        if message.msgid == 22:         # MAVLINK_MSG_ID_PARAM_VALUE
            self._handleIncomingParamValue(vehicle, message)
        elif message.msgid == 253:      # MAVLINK_MSG_ID_STATUSTEXT
            self._handleIncomingStatusText(vehicle, message)
        elif message.msgid == 0:        # MAVLINK_MSG_ID_HEARTBEAT
            self._handleIncomingHeartbeat(vehicle, message)
        return True

    def adjustOutgoingMavlinkMessage(self, vehicle, outgoingLink, message):
        # Don't process messages to/from UDP Bridge. It doesn't suffer from these issues
        if message.compid == 240:       # MAV_COMP_ID_UDP_BRIDGE
            return

        if message.msgid == 23:         # MAVLINK_MSG_ID_PARAM_SET
            self._handleOutgoingParamSet(vehicle, outgoingLink, message)

    def initializeVehicle(self, vehicle: Vehicle):
        if vehicle.isOfflineEditingVehicle():
            pass
        else:
            # Streams are not started automatically on APM stack
            vehicle.requestDataStream(1, 2)         # MAV_DATA_STREAM_RAW_SENSORS       1
            vehicle.requestDataStream(2, 2)         # MAV_DATA_STREAM_EXTENDED_STATUS   2
            vehicle.requestDataStream(3, 2)         # MAV_DATA_STREAM_RC_CHANNELS       3
            vehicle.requestDataStream(6, 3)         # MAV_DATA_STREAM_POSITION          6
            vehicle.requestDataStream(10, 10)       # MAV_DATA_STREAM_EXTRA1            10
            vehicle.requestDataStream(11, 10)       # MAV_DATA_STREAM_EXTRA2            11
            vehicle.requestDataStream(12, 3)        # MAV_DATA_STREAM_EXTRA3            12

    def sendHomePositionToVehicle(self):
        # APM stack wants the home position sent in the first position
        return True

    def addMetaDataToFact(self, parameterMetaData, fact, vehicleType):
        pass

    def missionCommandOverrides(self, vehicleType):
        switcher = {
            0: ':/json/APM/MavCmdInfoCommon.json',
            1: ':/json/APM/MavCmdInfoFixedWing.json',
            2: ':/json/APM/MavCmdInfoMultiRotor.json',
            20: ':/json/APM/MavCmdInfoVTOL.json',
            12: ':/json/APM/MavCmdInfoSub.json',
            10: ':/json/APM/MavCmdInfoRover.json',
        }
        s = switcher.get(vehicleType, None)
        if s:
            return s
        else:
            # qWarning() << "APMFirmwarePlugin::missionCommandOverrides called with bad MAV_TYPE:" << vehicleType;
            return ''

    def getVersionParam(self):
        return 'SYSID_SW_MREV'

    def internalParameterMetaDataFile(self, vehicle):
        pass

    def getParameterMetaDataVersionInfo(self, metaDataFile, majorVersion, minorVersion):
        # APMParameterMetaData::getParameterMetaDataVersionInfo(metaDataFile, majorVersion, minorVersion)
        pass

    def loadParameterMetaData(self, metaDataFile):
        pass

    def newGeoFenceManager(self, vehicle):
        # return new APMGeoFenceManager(vehicle)
        pass

    def newRallyPointManager(self, vehicle):
        # return new APMRallyPointManager(vehicle)
        pass

    def brandImageIndoor(self, vehicle):
        return '/qmlimages/APM/BrandImage'

    def brandImageOutdoor(self, vehicle):
        return '/qmlimages/APM/BrandImage'

# protected:
    #  All access to singleton is through stack specific implementation
    def __init__(self):
        super().__init__()
        self._coaxialMotors = False

    def setSupportedModes(self, supportedModes):
        self._supportedModes = supportedModes

# private:
    pass


class APMCopterMode(APMCustomMode):
    def __init__(self, mode, settable):
        super().__init__(mode, settable)
        enum_to_string = {
            0:  "Stabilize",
            1:  "Acro",
            2:  "Altitude Hold",
            3:  "Auto",
            4:  "Guided",
            5:  "Loiter",
            6:  "RTL",
            7:  "Circle",
            9:  "Land",
            11: "Drift",
            13: "Sport",
            14: "Flip",
            15: "Autotune",
            16: "Position Hold",
            17: "Brake",
            18: "Throw",
            19: "Avoid ADSB",
            20: "Guided No GPS",
        }
        self.setEnumToStringMapping(enum_to_string)


class ArduCopterFirmwarePlugin(APMFirmwarePlugin):
    def __init__(self):
        super().__init__()

        supported_flight_modes = [
            APMCopterMode(0, True),
            APMCopterMode(1, True),
            APMCopterMode(2, True),
            APMCopterMode(3, True),
            APMCopterMode(4, True),
            APMCopterMode(5, True),
            APMCopterMode(6, True),
            APMCopterMode(7, True),
            APMCopterMode(9, True),
            APMCopterMode(11, True),
            APMCopterMode(13, True),
            APMCopterMode(14, True),
            APMCopterMode(15, True),
            APMCopterMode(16, True),
            APMCopterMode(17, True),
            APMCopterMode(18, True),
            APMCopterMode(19, True),
            APMCopterMode(20, True)
        ]
        self.setSupportedModes(supported_flight_modes)

# Overrides from FirmwarePlugin
    def isCapable(self, vehicle, capabilities):
        vehicle_capabilities = 1 << 0 | 1 << 3 | 1 << 2
        # SetFlightModeCapability   1 << 0
        # GuidedModeCapability      1 << 3
        # PauseVehicleCapability    1 << 2
        return (capabilities & vehicle_capabilities) == capabilities

    def setGuidedMode(self, vehicle, guidedMode):
        if guidedMode:
            self._setFlightModeAndValidate(vehicle, 'Guided')
        else:
            self.pauseVehicle(vehicle)

    def pauseVehicle(self, vehicle):
        self._setFlightModeAndValidate(vehicle, "Brake")

    def guidedModeRTL(self, vehicle):
        self._setFlightModeAndValidate(vehicle, "RTL")

    def guidedModeLand(self, vehicle):
        self._setFlightModeAndValidate(vehicle, "Land")

    def guidedModeTakeoff(self, vehicle):
        self._guidedModeTakeoff(vehicle)

    def guidedModeGotoLocation(self, vehicle, gotoCoord: QGeoCoordinate):
        if vehicle.alt is None:
            # qgcApp()->showMessage(QStringLiteral("Unable to go to location, vehicle position not known."));
            return
        coordWithAltitude = gotoCoord
        coordWithAltitude.setAltitude(vehicle.alt)
        vehicle.missionManager().writeArduPilotGuidedMissionItem(coordWithAltitude, False)  # altChangeOnly

    def guidedModeChangeAltitude(self, vehicle, altitudeChange):
        if vehicle.alt is None:
            # qgcApp()->showMessage(QStringLiteral("Unable to go to location, vehicle position not known."));
            return
        self.setGuidedMode(vehicle, True)
        vehicle._mav.mav.set_position_target_local_ned_send(
            0,                              # time_boot_ms
            vehicle.id(),                   # target_system             : System ID (uint8_t)
            vehicle.defaultComponentId(),   # target_component          : Component ID (uint8_t)
            7,                              # coordinate_frame          : MAV_FRAME_LOCAL_OFFSET_NED = 7
            0xFFF8,                         # type_mask                 : Only x/y/z valid
            0,                              # x                         : X Position in NED frame in meters (float)
            0,                              # y                         : Y Position in NED frame in meters (float)
            -altitudeChange,                # z                         : Z Position in NED frame in meters (float)
            0,                              # vx                        : X velocity in NED frame in meter / s (float)
            0,                              # vy                        : Y velocity in NED frame in meter / s (float)
            0,                              # vz                        : Z velocity in NED frame in meter / s (float)
            0,                              # afx
            0,                              # afy
            0,                              # afz
            0,                              # yaw                       : yaw setpoint in rad (float)
            0                               # yaw_rate                  : yaw rate setpoint in rad/s (float)
        )

    def paramNameRemapMajorVersionMap(self):
        return self._remapParamName

    def remapParamNameHigestMinorVersionNumber(self, majorVersionNumber):
        # Remapping supports up to 3.5
        return 5 if majorVersionNumber == 3 else -1

    def multiRotorCoaxialMotors(self, vehicle):
        return self._coaxialMotors

    def multiRotorXConfig(self, vehicle):
        pass

    def geoFenceRadiusParam(self, vehicle):
        return 'FENCE_RADIUS'

    def offlineEditingParamFile(self, vehicle):
        return ':/FirmwarePlugin/APM/Copter.OfflineEditing.params'

    def pauseFlightMode(self):
        return 'Brake'

    def missionFlightMode(self):
        return 'Auto'

    def rtlFlightMode(self):
        return 'RTL'

    def landFlightMode(self):
        return 'Land'

    def takeControlFlightMode(self):
        return 'Stablize'

    def vehicleYawsToNextWaypointInMission(self, vehicle):
        pass
        return True

    def autoDisarmParameter(self, vehicle):
        return 'DISARM_DELAY'

    def startMission(self, vehicle):
        currentAlt = vehicle.alt
        if not vehicle.flying():
            if self._guidedModeTakeoff(vehicle):
                # Wait for vehicle to get off ground before switching to auto (10 seconds)
                didTakeoff = False
                q_thread = QThread()
                for i in range(100):
                    if vehicle.alt >= currentAlt + 1:
                        didTakeoff = True
                        break
                    q_thread.msleep(100)
                    QApplication.processEvents(QEventLoop.ExcludeUserInputEvents)
                if not didTakeoff:
                    # qgcApp()->showMessage(QStringLiteral("Unable to start mission. Vehicle takeoff failed."))
                    return
        if not self._setFlightModeAndValidate(vehicle, self.missionFlightMode()):
            # qgcApp()->showMessage(QStringLiteral("Unable to start mission. Vehicle failed to change to auto."))
            return

    def _guidedModeTakeoff(self, vehicle):
        takeoffAlt = 500

        if takeoffAlt <= 0:
            takeoffAlt = 2.5
        else:
            takeoffAlt /= 100

        if not self._setFlightModeAndValidate(vehicle, "Guided"):
            # qgcApp()->showMessage(tr("Unable to takeoff: Vehicle failed to change to Guided mode."));
            return False

        if not self._armVehicleAndValidate(vehicle):
            # qgcApp()->showMessage(tr("Unable to takeoff: Vehicle failed to arm."));
            return False

        vehicle.sendMavCommand(vehicle.defaultComponentId(),
                               22,                      # MAV_CMD_NAV_TAKEOFF
                               True,
                               0, 0, 0, 0, 0, 0,
                               takeoffAlt)
        return True


class ArduPlaneFirmwarePlugin(APMFirmwarePlugin):
    pass


class ArduRoverFirmwarePlugin(APMFirmwarePlugin):
    pass


class ArduSubFirmwarePlugin(APMFirmwarePlugin):
    pass


class FirmwarePluginFactory(QObject):
    def __init__(self):
        super().__init__()
        FirmwarePluginFactoryRegister().instance().registerPluginFactory(self)

    # Returns appropriate plugin for autopilot type.
    #     @param autopilotType Type of autopilot to return plugin for.
    #     @param vehicleType Vehicle type of autopilot to return plugin for.
    # @return Singleton FirmwarePlugin instance for the specified MAV_AUTOPILOT.
    def firmwarePluginForAutopilot(self, autopilotType, vehicleType) -> FirmwarePlugin:      # MAV_AUTOPILOT, MAV_TYPE
        pass

    # @return List of firmware types this plugin supports.
    def supportedFirmwareTypes(self) -> List[int]:                                          # MAV_AUTOPILOT
        pass

    # @return List of vehicle types this plugin supports
    def supportedVehicleTypes(self) -> List[int]:                                           # MAV_TYPE
        vehicleTypes = [
            1,          # MAV_TYPE_FIXED_WING
            2,          # MAV_TYPE_QUADROTOR
            20,         # MAV_TYPE_VTOL_QUADROTOR
            10,         # MAV_TYPE_GROUND_ROVER
            12,         # MAV_TYPE_SUBMARINE
        ]
        return vehicleTypes


class APMFirmwarePluginFactory(FirmwarePluginFactory):
    def __init__(self):
        super().__init__()
        self._arduCopterPluginInstance = None
        self._arduPlanePluginInstance = None
        self._arduRoverPluginInstance = None
        self._arduSubPluginInstance = None

    def supportedFirmwareTypes(self):
        vehicle_types = [
            3,          # MAV_AUTOPILOT_ARDUPILOTMEGA
        ]
        return vehicle_types

    def firmwarePluginForAutopilot(self, autopilotType, vehicleType):
        if autopilotType == 3:      # MAV_AUTOPILOT_ARDUPILOTMEGA   3
            if vehicleType in [
                2,                  # MAV_TYPE_QUADROTOR:
                13,                 # MAV_TYPE_HEXAROTOR:
                14,                 # MAV_TYPE_OCTOROTOR:
                15,                 # MAV_TYPE_TRICOPTER:
                3,                  # MAV_TYPE_COAXIAL:
                4,                  # MAV_TYPE_HELICOPTER:
            ]:
                if not self._arduCopterPluginInstance:
                    self._arduCopterPluginInstance = ArduCopterFirmwarePlugin()
                return self._arduCopterPluginInstance
            elif vehicleType in [
                1,                  # MAV_TYPE_FIXED_WING
            ]:
                if not self._arduPlanePluginInstance:
                    self._arduPlanePluginInstance = ArduPlaneFirmwarePlugin()
                return self._arduPlanePluginInstance
            elif vehicleType in [
                10,                 # MAV_TYPE_GROUND_ROVER:
                11,                 # MAV_TYPE_SURFACE_BOAT:
            ]:
                if not self._arduRoverPluginInstance:
                    self._arduRoverPluginInstance = ArduRoverFirmwarePlugin()
                return self._arduRoverPluginInstance
            elif vehicleType in [
                12,                 # MAV_TYPE_SUBMARINE:
            ]:
                if self._arduSubPluginInstance:
                    self._arduSubPluginInstance = ArduSubFirmwarePlugin
                return self._arduSubPluginInstance
            else:
                pass
        return None


class FirmwarePluginFactoryRegister(QObject):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self._factoryList = []

    def instance(self):
        global _instance
        if not _instance:
            _instance = FirmwarePluginFactoryRegister()
        return _instance

    # Registers the specified logging category to the system.
    def registerPluginFactory(self, pluginFactory: FirmwarePluginFactory):
        self._factoryList.append(pluginFactory)

    def pluginFactories(self):
        return self._factoryList
