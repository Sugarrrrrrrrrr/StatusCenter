import json
from typing import List

from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal, QTimer

from LinkInterface import LinkInterface
from Vehicle import Vehicle
from FirmwarePlugin import FirmwarePluginFactoryRegister, FirmwarePlugin, FirmwarePluginFactory, APMFirmwarePluginFactory


class scToolbox(QObject):
    def __init__(self, app, parent=None):
        super().__init__(parent=parent)
        self.parent = parent
        self.app = app

        if not parent:
            self._firmwarePluginMgr = FirmwarePluginManager(self.app, parent=self)
            self._multiVehicleMgr = MultiVehicleManager(self.app, parent=self)
            self._linkMgr = LinkManager(self.app, parent=self)

    def getLinkManager(self):
        return self._linkMgr

    def getFirmwarePluginManager(self):
        return self._firmwarePluginMgr


class LinkManager(scToolbox):
    def __init__(self, app, parent):
        super().__init__(app, parent=parent)

        self.uav_list = []
        self.links = []
        self.home_create = False
        self.home_lat = 39.9651391731
        self.home_lng = 116.3420835823

        self.update_links_name()

        for uav in self.uav_list:
            link = LinkInterface(uav, self.app, self)
            self.links.append(link)

            link.vehicleHeartbeatInfo.connect(parent._multiVehicleMgr._vehicleHeartbeatInfo)

    def update_links_name(self):
        with open('.config', 'r') as file:
            j = json.load(file)
            uavs = j['uavs']
            for uav in uavs:
                self.uav_list.append(uav)

    def set_home(self, lat, lng):
        self.home_create = True
        self.home_lat = lat
        self.home_lng = lng
        self.app.sc_map.set_home(self.home_lat, self.home_lng)
        self.app.sc_map.setCenter(self.home_lat, self.home_lng)


class MultiVehicleManager(scToolbox):
    def __init__(self, app, parent):
        super().__init__(app, parent=parent)
        self._vehicles = []
        self._ignoreVehicleIds = []
        self._gcsHeartbeatEnabled = True

        self._firmwarePluginManager = parent.getFirmwarePluginManager()

        self._gcsHeartbeatTimer = QTimer()
        self._gcsHeartbeatRateMSecs = 1000

        self._gcsHeartbeatTimer.setInterval(self._gcsHeartbeatRateMSecs)
        self._gcsHeartbeatTimer.setSingleShot(False)
        self._gcsHeartbeatTimer.timeout.connect(self._sendGCSHeartbeat)
        if self._gcsHeartbeatEnabled:
            self._gcsHeartbeatTimer.start()

# Signals
    vehicleAdded = pyqtSignal(object)  # vehicle
    gcsHeartBeatEnabledChanged = pyqtSignal(bool)

    @pyqtSlot(object, int, int, int, int, int)
    def _vehicleHeartbeatInfo(self, link, vehicleId, componentId, vehicleMavlinkVersion, vehicleFirmwareType,
                              vehicleType):
        if componentId != 1:  # MAV_COMP_ID_AUTOPILOT1    1
            # Don't create vehicles for components other than the autopilot
            if not self.getVehicleById(link, vehicleId):
                # qCDebug(MultiVehicleManagerLog()) << "Ignoring heartbeat from unknown component "
                #                                   << link->getName()
                #                                   << vehicleId
                #                                   << componentId
                #                                   << vehicleMavlinkVersion
                #                                   << vehicleFirmwareType
                #                                   << vehicleType;
                pass
            return

        if len(self._vehicles) > 0 and not self._multiVehicleEnabled():
            return

        if vehicleId in self._ignoreVehicleIds or self.getVehicleById(link, vehicleId) or vehicleId == 0:
            return

        if vehicleId in [6, 18, 26,
                         27]:  # MAV_TYPE_GCS 6, MAV_TYPE_ONBOARD_CONTROLLER 18, MAV_TYPE_GIMBAL 26, MAV_TYPE_ADSB 27
            return

        # qCDebug(MultiVehicleManagerLog())
        #   << "Adding new vehicle link:vehicleId:componentId:vehicleMavlinkVersion:vehicleFirmwareType:vehicleType "
        #   << link->getName()
        #   << vehicleId
        #   << componentId
        #   << vehicleMavlinkVersion
        #   << vehicleFirmwareType
        #   << vehicleType;

        #   if (vehicleId == _mavlinkProtocol->getSystemId()) {
        #       app->showMessage(QString("Warning: A vehicle is using the same system id as %1: %2")
        #                                                           .arg(qgcApp()->applicationName()).arg(vehicleId));
        #   }

        vehicle_name = None
        n = len(self._vehicles)
        while n>=0:
            vehicle_name = 'uav_' + str(n)
            if not self.getVehicleByName(vehicle_name):
                break
            n -= 1

        vehicle = Vehicle(self.app, link, vehicleId, componentId, vehicleFirmwareType, vehicleType,
                          self._firmwarePluginManager, vehicle_name=vehicle_name)
        # connect(vehicle, &Vehicle::allLinksInactive, this, &MultiVehicleManager::_deleteVehiclePhase1);
        # connect(vehicle->parameterManager(), &ParameterManager::parametersReadyChanged,
        #                                               this, &MultiVehicleManager::_vehicleParametersReadyChanged);
        self.app.mainWindow.add_para_widget(vehicle)
        self._vehicles.append(vehicle)
        self._sendGCSHeartbeat(vehicle)
        self.vehicleAdded.emit(vehicle)

    def _multiVehicleEnabled(self):
        # should get from qgcApp()->toolbox()->corePlugin()->options()->multiVehicleEnabled() dynamically
        return True

    def getVehicleById(self, link, vehicleId):
        for vehicle in self._vehicles:
            if vehicle.id() == vehicleId and vehicle.getLink() == link:
                return vehicle
        return None

    def getVehicleByName(self, vehicle_name):
        for vehicle in self._vehicles:
            if vehicle.vehicle_name == vehicle:
                return vehicle
        return None

    def _sendGCSHeartbeat(self, vehicle=None):
        if vehicle:     # Send a heartbeat out on the link of vehicle
            vehicle.sendHeartbeat()
        else:           # Send a heartbeat out on each link
            for vehicle in self._vehicles:
                vehicle.sendHeartbeat()

    def gcsHeartbeatEnabled(self):
        return self._gcsHeartbeatEnabled

    def setGcsHeartbeatEnabled(self, gcsHeartBeatEnabled):
        if gcsHeartBeatEnabled != self._gcsHeartbeatEnabled:
            self._gcsHeartbeatEnabled = gcsHeartBeatEnabled
            self.gcsHeartBeatEnabledChanged.emit(gcsHeartBeatEnabled)

            if gcsHeartBeatEnabled:
                self._gcsHeartbeatTimer.start()
            else:
                self._gcsHeartbeatTimer.stop()


class FirmwarePluginManager(scToolbox):
    # FirmwarePluginManager is a singleton which is used to return the correct FirmwarePlugin for a MAV_AUTOPILOT type.
    def __init__(self, app, parent):
        super().__init__(app, parent=parent)

        self._genericFirmwarePlugin = None
        self._supportedFirmwareTypes = []

        # Register Plugin Factories
        APMFirmwarePluginFactory()
        FirmwarePluginFactory()

    def __del__(self):
        del self._genericFirmwarePlugin

    # Returns list of firmwares which are supported by the system
    def supportedFirmwareTypes(self) -> List[int]:                      # MAV_AUTOPILOT
        if not self._supportedFirmwareTypes:                            # self._supportedFirmwareTypes is []
            factoryList = FirmwarePluginFactoryRegister.instance(None).pluginFactories()
            # type: List[FirmwarePluginFactory]
            for factory in factoryList:
                self._supportedFirmwareTypes.append(factory.supportedFirmwareTypes())
            self._supportedFirmwareTypes.append(0)                  # MAV_AUTOPILOT_GENERIC     0
        return self._supportedFirmwareTypes

    # Returns the list of supported vehicle types for the specified firmware
    def supportedVehicleTypes(self, firmwareType) -> List[int]:         # MAV_TYPE
        vehicleTypes = []
        factory = self._findPluginFactory(firmwareType)
        if factory:
            vehicleTypes = factory.supportedVehicleTypes()
        elif firmwareType == 0:                                     # MAV_AUTOPILOT_GENERIC     0
            vehicleTypes = [
                1,          # MAV_TYPE_FIXED_WING
                2,          # MAV_TYPE_QUADROTOR
                20,         # MAV_TYPE_VTOL_QUADROTOR
                10,         # MAV_TYPE_GROUND_ROVER
                12          # MAV_TYPE_SUBMARINE
            ]
        else:
            # qWarning() << "Request for unknown firmware plugin factory" << firmwareType;
            pass

        return vehicleTypes

    # Returns appropriate plugin for autopilot type.
    #   @param firmwareType Type of firmwware to return plugin for.
    #   @param vehicleType Vehicle type to return plugin for.
    # @return Singleton FirmwarePlugin instance for the specified MAV_AUTOPILOT.
    def firmwarePluginForAutopilot(self, firmwareType, vehicleType):    # MAV_AUTOPILOT, MAV_TYPE vehicleType
        factory = self._findPluginFactory(firmwareType)                 # type: FirmwarePluginFactory
        plugin = None                                                   # type: FirmwarePlugin

        if factory:
            plugin = factory.firmwarePluginForAutopilot(firmwareType, vehicleType)
        elif firmwareType != 0:                                         # MAV_AUTOPILOT_GENERIC     0
            # qWarning() << "Request for unknown firmware plugin factory" << firmwareType;
            pass

        if not plugin:
            # Default plugin fallback
            if not self._genericFirmwarePlugin:
                self._genericFirmwarePlugin = FirmwarePlugin()
            plugin = self._genericFirmwarePlugin

        return plugin

    def _findPluginFactory(self, firmwareType) -> FirmwarePluginFactory:
        factoryList = FirmwarePluginFactoryRegister.instance(None).pluginFactories()    # type: List[FirmwarePluginFactory]
        # Find the plugin which supports this vehicle
        for factory in factoryList:
            if firmwareType in factory.supportedFirmwareTypes():
                return factory
        return None
