from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QTimer
from PyQt5.QtPositioning import QGeoCoordinate

from enum import Enum
from typing import List

from MissionManager.MissionItem import MissionItem
from comm.LinkInterface import LinkInterface


class ErrorCode(Enum):
    InternalError = 1
    AckTimeoutError = 2        # Timed out waiting for response from vehicle
    ProtocolOrderError = 3     # Incorrect protocol sequence from vehicle
    RequestRangeError = 4      # Vehicle requested item out of range
    ItemMismatchError = 5      # Vehicle returned item with seq # different than requested
    VehicleError = 6           # Vehicle returned error
    MissingRequestsError = 7   # Vehicle did not request all items during write sequence
    MaxRetryExceeded = 8       # Retry failed


class AckType(Enum):
    AckNone = 1                 # State machine is idle
    AckMissionCount = 2         # MISSION_COUNT message expected
    AckMissionItem = 3          # MISSION_ITEM expected
    AckMissionRequest = 4       # MISSION_REQUEST is expected, or MISSION_ACK to end sequence
    AckMissionClearAll = 5      # MISSION_CLEAR_ALL sent, MISSION_ACK is expected
    AckGuidedItem = 6           # MISSION_ACK expected in response to ArduPilot guided mode single item send


class TransactionType(Enum):
    TransactionNone = 1
    TransactionRead = 2
    TransactionWrite = 3
    TransactionRemoveAll = 4


class MissionManager(QObject):
    def __init__(self, linkInterface):
        self._vehicle = None                                                # _vehicle type: Vehicle
        self._linkInterface = linkInterface                                 # type: LinkInterface
        self._mav = self._linkInterface.mav
        self._ackTimeoutTimer = None                                        # type: QTimer
        self._expectedAck = AckType.AckNone                                 # type: AckType
        self._transactionInProgress = TransactionType.TransactionNone       # type: TransactionType
        self._resumeMission = False                                         # type: bool
        # Index of item last requested by MISSION_REQUEST
        self._lastMissionRequest = -1                                       # type: int
        self._currentMissionIndex = -1                                      # type: int
        self._lastCurrentIndex = -1                                         # type: int
        self._cachedLastCurrentIndex = -1                                   # type: int

        self._retryCount = 0                                                # type: int

        # Set of mission items currently being written to vehicle
        self._writeMissionItems = []                                        # type: List[MissionItem]

        '''
        QList<int>          _itemIndicesToWrite;    ///< List of mission items which still need to be written to vehicle
        QList<int>          _itemIndicesToRead;     ///< List of mission items which still need to be requested from vehicle
    
        QMutex _dataMutex;
    
        QList<MissionItem*> _missionItems;          ///< Set of mission items on vehicle
        '''

        # connect(_vehicle, &Vehicle::mavlinkMessageReceived, this, &MissionManager::_mavlinkMessageReceived);

        self._ackTimeoutTimer = QTimer(self)
        self._ackTimeoutTimer.setSingleShot(True)
        self._ackTimeoutTimer.setInterval(self._ackTimeoutMilliseconds)

        self._ackTimeoutTimer.timeout.connect(self._ackTimeout)

    def __del__(self):
        pass

# public:
    def inProgress(self) -> bool:
        return self._transactionInProgress != TransactionType.TransactionNone

    def missionItems(self) -> List[MissionItem]:
        return self._missionItems

    # Current mission item as reported by MISSION_CURRENT
    def currentIndex(self) -> int:
        return self._currentMissionIndex

    # Last current mission item reported while in Mission flight mode
    def lastCurrentIndex(self) -> int:
        return self._lastCurrentIndex

    # Load the mission items from the vehicle
    #   Signals newMissionItemsAvailable when done
    def loadFromVehicle(self):
        # if _vehicle.isOfflineEditingVehicle():
        #     return

        # qCDebug(MissionManagerLog) << "loadFromVehicle read sequence";

        if self.inProgress():
            # qCDebug(MissionManagerLog) << "loadFromVehicle called while transaction in progress";
            return

        self._retryCount = 0
        self._transactionInProgress = TransactionType.TransactionRead
        self.inProgressChanged.emit()
        self._requestList()

    # Writes the specified set of mission items to the vehicle
    #   @param missionItems Items to send to vehicle
    #   Signals sendComplete when done
    def writeMissionItems(self, missionItems: List[MissionItem]):
        # if _vehicle.isOfflineEditingVehicle():
        #     return

        if self.inProgress():
            # qCDebug(MissionManagerLog) << "writeMissionItems called while transaction in progress";
            return

        self._clearAndDeleteWriteMissionItems()

        # bool skipFirstItem = !_vehicle->firmwarePlugin()->sendHomePositionToVehicle();
        skipFirstItem = False
        # int firstIndex = skipFirstItem ? 1 : 0;
        firstIndex = 0

        for i in range(firstIndex, len(missionItems)):
            item = missionItems[i]
            self._writeMissonItems.append(item)

            item.setIsCurrentItem(i == firstIndex)

            if skipFirstItem:
                # Home is in sequence 0, remainder of items start at sequence 1
                item.setSequenceNumber(item.sequenceNumber() - 1)
                if item.command() == 177:           # MAV_CMD_DO_JUMP 177
                    item.setParam1(int(item.param1()) - 1)

        self._writeMissionItemsWorker()


    # Writes the specified set mission items to the vehicle as an ArduPilot guided mode mission item.
    #   @param gotoCoord Coordinate to move to
    #   @param altChangeOnly true: only altitude change, false: lat/lon/alt change
    def writeArduPilotGuidedMissionItem(self, gotoCoord: QGeoCoordinate, altChangeOnly: bool):
        if self.inProgress():
            # qCDebug(MissionManagerLog) << "writeArduPilotGuidedMissionItem called while transaction in progress";
            return

        self._transactionInProgress = TransactionType.TransactionWrite

        # memset(&missionItem, 8, sizeof(missionItem));
        # missionItem.target_system =     _vehicle->id();
        # missionItem.target_component =  _vehicle->defaultComponentId();
        # missionItem.seq =               0;
        # missionItem.command =           MAV_CMD_NAV_WAYPOINT;
        # missionItem.param1 =            0;
        # missionItem.param2 =            0;
        # missionItem.param3 =            0;
        # missionItem.param4 =            0;
        # missionItem.x =                 gotoCoord.latitude();
        # missionItem.y =                 gotoCoord.longitude();
        # missionItem.z =                 gotoCoord.altitude();
        # missionItem.frame =             MAV_FRAME_GLOBAL_RELATIVE_ALT;
        # missionItem.current =           altChangeOnly ? 3 : 2;
        # missionItem.autocontinue =      true;


        self._mav.mav.mission_item_send(
            self._linkInterface.id(),                   # target_system
            self._linkInterface.defaultComponentId(),   # target_component
            0,                                          # seq
            3,                                          # frame                 MAV_FRAME_GLOBAL_RELATIVE_ALT 3
            16,                                         # command               MAV_CMD_NAV_WAYPOINT 16
            3 if altChangeOnly else 2,                  # current               : false:0, true:1 (uint8_t)
            1,                                          # autocontinue
            0,                                          # param1
            0,                                          # param2
            0,                                          # param3
            0,                                          # param4
            gotoCoord.latitude(),                       # x
            gotoCoord.longitude(),                      # y
            gotoCoord.altitude()                        # z
        )

        self._startAckTimeout(AckType.AckGuidedItem)
        self.inProgressChanged.emit(True)




    # Removes all mission items from vehicle
    #   Signals removeAllComplete when done
    def removeAll(self):
        if self.inProgress():
            return

        # qCDebug(MissionManagerLog) << "removeAll";

        self._clearAndDeleteMissionItems()

        self._currentMissionIndex = -1
        self._lastCurrentIndex = -1
        self._cachedLastCurrentIndex = -1
        self.currentIndexChanged.emit(-1)
        self.lastCurrentIndexChanged.emit(-1)

        self._transactionInProgress = TransactionType.TransactionRemoveAll
        self._retryCount = 0
        self.inProgressChanged.emit(True)

        self._removeAllWorker()


    # Generates a new mission which starts from the specified index. It will include all the CMD_DO items
    # from mission start to resumeIndex in the generate mission.
    def generateResumeMission(self, resumeIndex: int):
        pass

    _ackTimeoutMilliseconds = 1000
    _maxRetryCount = 5

# signals:
    newMissionItemsAvailable = pyqtSignal(bool)     # removeAllRequested
    inProgressChanged = pyqtSignal(bool)            # inProgress
    error = pyqtSignal(int, str)                    # errorCode, errorMsg
    currentIndexChanged = pyqtSignal(int)           # currentIndex
    lastCurrentIndexChanged = pyqtSignal(int)       # lastCurrentIndex
    resumeMissionReady = pyqtSignal()
    resumeMissionUploadFail = pyqtSignal()
    progressPct = pyqtSignal(float)                 # progressPercentPct
    removeAllComplete = pyqtSignal(bool)            # error
    sendComplete = pyqtSignal(bool)                 # error

# slots:
    # Called when a new mavlink message for out vehicle is received
    @pyqtSlot(object)
    def _mavlinkMessageReceived(self, message):                             # message type: mavlink_message_t
        msgId = message.get_msgId()
        switcher = {
            44: lambda: self._handleMissionCount(message),                  # MAVLINK_MSG_ID_MISSION_COUNT          44
            39: lambda: self._handleMissionItem(message, False),            # MAVLINK_MSG_ID_MISSION_ITEM           39
            73: lambda: self._handleMissionItem(message, True),             # MAVLINK_MSG_ID_MISSION_ITEM_INT       73
            40: lambda: self._handleMissionRequest(message, False),         # MAVLINK_MSG_ID_MISSION_REQUEST        40
            51: lambda: self._handleMissionRequest(message, True),          # MAVLINK_MSG_ID_MISSION_REQUEST_INT    51
            47: lambda: self._handleMissionAck(message),                    # MAVLINK_MSG_ID_MISSION_ACK            47
            46: lambda: 'FIXME: NYI',                                       # MAVLINK_MSG_ID_MISSION_ITEM_REACHED   46
            42: lambda: self._handleMissionCurrent(message),                # MAVLINK_MSG_ID_MISSION_CURRENT        42
            0: lambda: self._handleHeartbeat(message),                      # MAVLINK_MSG_ID_HEARTBEAT               0
        }
        switcher.get(msgId, lambda *args: 'nothing')()

    @pyqtSlot()
    def _ackTimeout(self):
        ---
        pass

    # private
    def _startAckTimeout(self, ack: AckType):
        pass

    def _checkForExpectedAck(self, receivedAck: AckType) -> bool:
        pass

    def _readTransactionComplete(self):
        pass

    def _handleMissionCount(self, message):                             # message type: mavlink_message_t
        pass

    def _handleMissionItem(self, message, missionItemInt: bool):        # message type: mavlink_message_t
        pass

    def _handleMissionRequest(self, message, missionItemInt: bool):     # message type: mavlink_message_t
        pass

    def _handleMissionAck(self, message):                               # message type: mavlink_message_t
        pass

    def _handleMissionCurrent(self, message):                           # message type: mavlink_message_t
        pass

    def _handleHeartbeat(self, message):                                # message type: mavlink_message_t
        pass

    def _requestNextMissionItem(self):
        pass

    def _clearMissionItems(self):
        pass

    def _sendError(self, errorCode: ErrorCode, errorMsg: str):
        pass

    def _ackTypeToString(self, ackType: AckType) -> str:
        pass

    def _missionResultToString(self, result) -> str:    # result: type MAV_MISSION_RESULT
        pass

    def _finishTransaction(self, success: bool):
        pass

    def _requestList(self):
        pass

    def _writeMissionCount(self):
        pass

    def _writeMissionItemsWorker(self):
        pass

    def _clearAndDeleteMissionItems(self):
       pass

    def _clearAndDeleteWriteMissionItems(self):
        pass

    def _lastMissionReqestString(self, result) -> str:  # result: type MAV_MISSION_RESULT
        pass

    def _removeAllWorker(self):
        pass

