from PyQt5.QtCore import QObject
from typing import List

from Vehicle import Vehicle

_instance = None


class FirmwarePlugin(QObject):
    def initializeVehicle(self, vehicle: Vehicle):
        # Generic Flight Stack is by definition "generic", so no extra work
        pass

    def isCapable(self, vehicle, capabilities):
        pass

    def flightModes(self, vehicle):
        pass

    def setFlightMode(self, flightMode, base_mode, custom_mode):
        # qWarning() << "FirmwarePlugin::setFlightMode called on base class, not supported"
        return False


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

    def setSupportedModes(self, supportedModes):
        self._supportedModes = supportedModes


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

    def isCapable(self, vehicle, capabilities):
        vehicle_capabilities = 1 << 0 | 1 << 3 | 1 << 2
        # SetFlightModeCapability   1 << 0
        # GuidedModeCapability      1 << 3
        # PauseVehicleCapability    1 << 2
        return (capabilities & vehicle_capabilities) == capabilities


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
