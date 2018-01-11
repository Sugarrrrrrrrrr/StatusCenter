import json
from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal, QTimer
from LinkInterface import LinkInterface
from Vehicle import Vehicle


class scToolbox(QObject):
    def __init__(self, app, parent=None):
        super().__init__(parent=parent)
        self.parent = parent
        self.app = app

        if not self.parent:
            self._multiVehicleManager = MultiVehicleManager(self.app, parent=self)
            self.linkMgr = LinkManager(self.app, parent=self)


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

            link.vehicleHeartbeatInfo.connect(parent._multiVehicleManager._vehicleHeartbeatInfo)

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

        vehicle = Vehicle(self.app, link, vehicleId, componentId, vehicle_name=vehicle_name)
        # connect(vehicle, &Vehicle::allLinksInactive, this, &MultiVehicleManager::_deleteVehiclePhase1);
        # connect(vehicle->parameterManager(), &ParameterManager::parametersReadyChanged,
        #                                               this, &MultiVehicleManager::_vehicleParametersReadyChanged);
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
            vehicle.sendHearbet()
        else:           # Send a heartbeat out on each link
            for vehicle in self._vehicles:
                vehicle.sendHearbet()

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
