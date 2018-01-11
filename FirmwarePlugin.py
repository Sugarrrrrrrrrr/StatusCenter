from PyQt5.QtCore import QObject
from typing import List

from Vehicle import Vehicle

_instance = None


class FirmwarePlugin(QObject):
    def initializeVehicle(self, vehicle: Vehicle):
        # Generic Flight Stack is by definition "generic", so no extra work
        pass


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

class ArduCopterFirmwarePlugin(APMFirmwarePlugin):
    pass

class ArduPlaneFirmwarePlugin(APMFirmwarePlugin):
    pass

class ArduRoverFirmwarePlugin(APMFirmwarePlugin):
    pass

class ArduSubFirmwarePlugin(APMFirmwarePlugin):
    pass

class FirmwarePluginFactory(QObject):
    def __init__(self):
        FirmwarePluginFactoryRegister.instance(None).registerPluginFactory(self)

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
        vehicleTypes = [
            3,          # MAV_AUTOPILOT_ARDUPILOTMEGA
        ]
        return vehicleTypes

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
