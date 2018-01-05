from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QTimer
from PyQt5.QtPositioning import QGeoCoordinate

from enum import Enum
from typing import List

from MissionManager.MissionItem import MissionItem
from comm.LinkInterface import LinkInterface


class ErrorCode(Enum):
    InternalError = 1
    AckTimeoutError = 2  # Timed out waiting for response from vehicle
    ProtocolOrderError = 3  # Incorrect protocol sequence from vehicle
    RequestRangeError = 4  # Vehicle requested item out of range
    ItemMismatchError = 5  # Vehicle returned item with seq # different than requested
    VehicleError = 6  # Vehicle returned error
    MissingRequestsError = 7  # Vehicle did not request all items during write sequence
    MaxRetryExceeded = 8  # Retry failed


class AckType(Enum):
    AckNone = 1  # State machine is idle
    AckMissionCount = 2  # MISSION_COUNT message expected
    AckMissionItem = 3  # MISSION_ITEM expected
    AckMissionRequest = 4  # MISSION_REQUEST is expected, or MISSION_ACK to end sequence
    AckMissionClearAll = 5  # MISSION_CLEAR_ALL sent, MISSION_ACK is expected
    AckGuidedItem = 6  # MISSION_ACK expected in response to ArduPilot guided mode single item send


class TransactionType(Enum):
    TransactionNone = 1
    TransactionRead = 2
    TransactionWrite = 3
    TransactionRemoveAll = 4


class MissionManager(QObject):
    def __init__(self, linkInterface):
        self._vehicle = None  # _vehicle type: Vehicle
        self._linkInterface = linkInterface  # type: LinkInterface
        self._mav = self._linkInterface.mav
        self._ackTimeoutTimer = None  # type: QTimer
        self._expectedAck = AckType.AckNone  # type: AckType
        self._transactionInProgress = TransactionType.TransactionNone  # type: TransactionType
        self._resumeMission = False  # type: bool
        # Index of item last requested by MISSION_REQUEST
        self._lastMissionRequest = -1  # type: int
        self._currentMissionIndex = -1  # type: int
        self._lastCurrentIndex = -1  # type: int
        self._cachedLastCurrentIndex = -1  # type: int

        self._retryCount = 0  # type: int

        # Set of mission items currently being written to vehicle
        self._writeMissionItems = []  # type: List[MissionItem]
        # Set of mission items on vehicle
        self._missionItems = []  # type: List[MissionItem]

        # List of mission items which still need to be written to vehicle
        self._itemIndicesToWrite = []  # type: List[int]
        # List of mission items which still need to be requested from vehicle
        self._itemIndicesToRead = []  # type: List[int]

        # QMutex _dataMutex;

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
                if item.command() == 177:  # MAV_CMD_DO_JUMP 177
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
            self._linkInterface.id(),  # target_system
            self._linkInterface.defaultComponentId(),  # target_component
            0,  # seq
            3,  # frame                 MAV_FRAME_GLOBAL_RELATIVE_ALT 3
            16,  # command               MAV_CMD_NAV_WAYPOINT 16
            3 if altChangeOnly else 2,  # current               : false:0, true:1 (uint8_t)
            1,  # autocontinue
            0,  # param1
            0,  # param2
            0,  # param3
            0,  # param4
            gotoCoord.latitude(),  # x
            gotoCoord.longitude(),  # y
            gotoCoord.altitude()  # z
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
        def wirteHere():
            pass

    _ackTimeoutMilliseconds = 1000
    _maxRetryCount = 5

    # signals:
    newMissionItemsAvailable = pyqtSignal(bool)  # removeAllRequested
    inProgressChanged = pyqtSignal(bool)  # inProgress
    error = pyqtSignal(int, str)  # errorCode, errorMsg
    currentIndexChanged = pyqtSignal(int)  # currentIndex
    lastCurrentIndexChanged = pyqtSignal(int)  # lastCurrentIndex
    resumeMissionReady = pyqtSignal()
    resumeMissionUploadFail = pyqtSignal()
    progressPct = pyqtSignal(float)  # progressPercentPct
    removeAllComplete = pyqtSignal(bool)  # error
    sendComplete = pyqtSignal(bool)  # error

    # slots:
    # Called when a new mavlink message for out vehicle is received
    @pyqtSlot(object)
    def _mavlinkMessageReceived(self, message):  # message type: mavlink_message_t
        msgId = message.get_msgId()
        switcher = {
            44: lambda: self._handleMissionCount(message),  # MAVLINK_MSG_ID_MISSION_COUNT          44
            39: lambda: self._handleMissionItem(message, False),  # MAVLINK_MSG_ID_MISSION_ITEM           39
            73: lambda: self._handleMissionItem(message, True),  # MAVLINK_MSG_ID_MISSION_ITEM_INT       73
            40: lambda: self._handleMissionRequest(message, False),  # MAVLINK_MSG_ID_MISSION_REQUEST        40
            51: lambda: self._handleMissionRequest(message, True),  # MAVLINK_MSG_ID_MISSION_REQUEST_INT    51
            47: lambda: self._handleMissionAck(message),  # MAVLINK_MSG_ID_MISSION_ACK            47
            46: lambda: 'FIXME: NYI',  # MAVLINK_MSG_ID_MISSION_ITEM_REACHED   46
            42: lambda: self._handleMissionCurrent(message),  # MAVLINK_MSG_ID_MISSION_CURRENT        42
            0: lambda: self._handleHeartbeat(message),  # MAVLINK_MSG_ID_HEARTBEAT               0
        }
        switcher.get(msgId, lambda *args: 'nothing')()

    @pyqtSlot()
    def _ackTimeout(self):
        if self._expectedAck == AckType.AckNone:
            return

        def _handleAckNoneTimeout():
            # qCWarning(MissionManagerLog) << "_ackTimeout timeout with AckNone";
            self._sendError(ErrorCode.InternalError, "Internal error occurred during Mission Item communication: "
                                                     "_ackTimeOut:_expectedAck == AckNone")

        def _handleAckMissionCountTimeout():
            # MISSION_COUNT message expected
            if self._retryCount > self._maxRetryCount:
                self._sendError(ErrorCode.VehicleError, "Mission request list failed, maximum retries exceeded.")
                self._finishTransaction(False)
            else:
                self._retryCount += 1
                # qCDebug(MissionManagerLog) << "Retrying REQUEST_LIST retry Count" << _retryCount;
                self._requestList()

        def _handleAckMissionItemTimeout():
            # MISSION_ITEM expected
            if self._retryCount > self._maxRetryCount:
                self._sendError(ErrorCode.VehicleError, "Mission read failed, maximum retries exceeded.")
                self._finishTransaction(False)
            else:
                self._retryCount += 1
                # qCDebug(MissionManagerLog) << "Retrying MISSION_REQUEST retry Count" << _retryCount;
                self._requestNextMissionItem()

        def _handleAckMissionRequestTimeout():
            # MISSION_REQUEST is expected, or MISSION_ACK to end sequence
            if len(self._itemIndicesToWrite) == 0:
                # Vehicle did not send final MISSION_ACK at end of sequence
                self._sendError(ErrorCode.VehicleError, "Mission write failed, vehicle failed to send final ack.")
                self._finishTransaction(False)
            elif self._itemIndicesToWrite[0] == 0:
                # Vehicle did not respond to MISSION_COUNT, try again
                if self._retryCount > self._maxRetryCount:
                    self._sendError(ErrorCode.VehicleError, "Mission write mission count failed, maximum retries "
                                                            "exceeded.")
                    self._finishTransaction(False)
                else:
                    self._retryCount += 1
                    # qCDebug(MissionManagerLog) << "Retrying MISSION_COUNT retry Count" << _retryCount;
                    self._writeMissionCount()
            else:
                # Vehicle did not request all items from ground station
                self._sendError(ErrorCode.AckTimeoutError, "Vehicle did not request all items from ground station: %s"
                                % str(self._expectedAck))
                self._expectedAck = AckType.AckNone
                self._finishTransaction(False)

        def _handleAckMissionClearAllTimeout():
            # MISSION_ACK expected
            if self._retryCount > self._maxRetryCount:
                self._sendError(ErrorCode.VehicleError, "Mission remove all, maximum retries exceeded.")
                self._finishTransaction(False)
            else:
                self._retryCount += 1
                # qCDebug(MissionManagerLog) << "Retrying MISSION_CLEAR_ALL retry Count" << _retryCount;
                self._removeAllWorker()

        def _handleAckGuidedItemTimeout():
            # MISSION_REQUEST is expected, or MISSION_ACK to end sequence
            pass

        def _handleDefaultTimeout():
            self._sendError(ErrorCode.VehicleError, "Vehicle did not respond to mission item communication: %s"
                            % str(self._expectedAck))

        switcher = {
            AckType.AckNone: _handleAckNoneTimeout,
            AckType.AckMissionCount: _handleAckMissionCountTimeout,
            AckType.AckMissionItem: _handleAckMissionItemTimeout,
            AckType.AckMissionRequest: _handleAckMissionRequestTimeout,
            AckType.AckMissionClearAll: _handleAckMissionClearAllTimeout,
            AckType.AckGuidedItem: _handleAckGuidedItemTimeout,
        }
        switcher.get(self._expectedAck, _handleDefaultTimeout)()

    # private
    def _startAckTimeout(self, ack: AckType):
        self._expectedAck = ack
        self._ackTimeoutTimer.start()

    # Checks the received ack against the expected ack. If they match the ack timeout timer will be stopped.
    # @return true: received ack matches expected ack
    def _checkForExpectedAck(self, receivedAck: AckType) -> bool:
        if receivedAck == self._expectedAck:
            self._expectedAck = AckType.AckNone
            self._ackTimeoutTimer.stop()
            return True
        else:
            if self._expectedAck == AckType.AckNone:
                # Don't worry about unexpected mission commands, just ignore them; ArduPilot updates home position using
                # spurious MISSION_ITEMs.
                pass
            else:
                # We just warn in this case, this could be crap left over from a previous transaction or the vehicle
                #       going bonkers.
                # Whatever it is we let the ack timeout handle any error output to the user.

                # qCDebug(MissionManagerLog) << QString("Out of sequence ack expected:received %1:%2")
                #       .arg(_ackTypeToString(_expectedAck)).arg(_ackTypeToString(receivedAck));
                pass
            return False

    def _readTransactionComplete(self):
        # qCDebug(MissionManagerLog) << "_readTransactionComplete read sequence complete";
        self._mav.mav.mission_ack_send(
            self._linkInterface.id(),  # target_system
            190,  # target_component          MAV_COMP_ID_MISSIONPLANNER  190
            0  # type                      MAV_MISSION_ACCEPTED          0
        )
        self._finishTransaction(True)

    def _handleMissionCount(self, message):  # message type: mavlink_message_t
        missonCount = message
        if not self._checkForExpectedAck(AckType.AckMissionCount):
            return

        self._retryCount = 0
        # qCDebug(MissionManagerLog) << "_handleMissionCount count:" << missionCount.count;
        if missonCount.count == 0:
            self._readTransactionComplete()
        else:
            # Prime read list
            self._itemIndicesToRead = [i for i in range(missonCount.count)]
            self._requestNextMissionItem()

    def _handleMissionItem(self, message, missionItemInt: bool):  # message type: mavlink_message_t
        missionItem = message
        if missionItemInt:
            command = missionItem.command
            frame = missionItem.frame
            param1 = missionItem.param1
            param2 = missionItem.param2
            param3 = missionItem.param3
            param4 = missionItem.param4
            param5 = missionItem.x / (10 ** 7)
            param6 = missionItem.y / (10 ** 7)
            param7 = missionItem.z
            autoContinue = missionItem.autocontinue
            isCurrentItem = missionItem.current
            seq = missionItem.seq
        else:
            command = missionItem.command
            frame = missionItem.frame
            param1 = missionItem.param1
            param2 = missionItem.param2
            param3 = missionItem.param3
            param4 = missionItem.param4
            param5 = missionItem.x
            param6 = missionItem.y
            param7 = missionItem.z
            autoContinue = missionItem.autocontinue
            isCurrentItem = missionItem.current
            seq = missionItem.seq

        # We don't support editing ALT_INT frames so change on the way in.
        if frame == 5:  # MAV_FRAME_GLOBAL_INT                  5
            frame = 0  # MAV_FRAME_GLOBAL                      0
        elif frame == 6:  # MAV_FRAME_GLOBAL_RELATIVE_ALT_INT     6
            frame = 3  # MAV_FRAME_GLOBAL_RELATIVE_ALT         3

        ardupilotHomePositionUpdate = False
        if not self._checkForExpectedAck(AckType.AckMissionItem):
            if self._linkInterface.apmFirmware() and seq == 0:
                ardupilotHomePositionUpdate = True
            else:
                # qCDebug(MissionManagerLog) << "_handleMissionItem dropping spurious item seq:command:current"
                #       << seq << command << isCurrentItem;
                return

        # qCDebug(MissionManagerLog) << "_handleMissionItem seq:command:current:ardupilotHomePositionUpdate"
        #       << seq << command << isCurrentItem << ardupilotHomePositionUpdate;

        if ardupilotHomePositionUpdate:
            self._linkInterface.setHomePosition(param5, param6, param7)
            return

        if seq in self._itemIndicesToRead:
            self._itemIndicesToRead.remove(seq)

            item = MissionItem()
            item.setSequenceNumber(seq)
            item.setCommand(command)
            item.setFrame(frame)
            item.setParam1(param1)
            item.setParam2(param2)
            item.setParam3(param3)
            item.setParam4(param4)
            item.setParam5(param5)
            item.setParam6(param6)
            item.setParam7(param7)
            item.setAutoContinue(autoContinue)
            item.setIsCurrentItem(isCurrentItem)

            if item.command() == 177 and not self._linkInterface.sendHomePositionToVehicle():  # MAV_CMD_DO_JUMP   177
                # Home is in position 0
                item.setParam1(item.param1() + 1)

            self._missionItems.append(item)
        else:
            # qCDebug(MissionManagerLog) << "_handleMissionItem mission item received item index which was not requested, disregrarding:" << seq;
            # We have to put the ack timeout back since it was removed above
            self._startAckTimeout(AckType.AckGuidedItem)
            return

        self.progressPct.emit(seq / len(self._missionItems))

        self._retryCount = 0
        if len(self._itemIndicesToRead) == 0:
            self._readTransactionComplete()
        else:
            self._requestNextMissionItem()

    def _handleMissionRequest(self, message, missionItemInt: bool):  # message type: mavlink_message_t
        missionRequest = message
        if not self._checkForExpectedAck(AckType.AckMissionRequest):
            return

        # qCDebug(MissionManagerLog) << "_handleMissionRequest sequenceNumber" << missionRequest.seq;

        if missionRequest.seq > len(self._writeMissionItems) - 1:
            self._sendError(
                ErrorCode.RequestRangeError,
                "Vehicle requested item outside range, count:request %s:%s. Send to Vehicle failed." %
                (len(self._writeMissionItems), missionRequest.seq)
            )
            self._finishTransaction(False)
            return

        self.progressPct.emit(missionRequest.seq / len(self._writeMissionItems))

        self._lastMissionRequest = missionRequest.seq
        if not missionRequest.seq in self._itemIndicesToWrite:
            # qCDebug(MissionManagerLog) << "_handleMissionRequest sequence number requested which has already
            #       been sent, sending again:" << missionRequest.seq;
            pass
        else:
            self._itemIndicesToWrite.remove(missionRequest.seq)

        item = self._writeMissionItems[missionRequest.seq]
        # qCDebug(MissionManagerLog) << "_handleMissionRequest sequenceNumber:command" << missionRequest.seq
        #       << item->command();

        if missionItemInt:
            self._mav.mav.mission_item_int_send(
                self._linkInterface.id(),  # target_system
                190,  # target_component      MAV_COMP_ID_MISSIONPLANNER      190
                missionRequest.seq,  # seq
                item.frame(),  # frame
                item.command(),  # command
                1 if missionRequest.seq == 0 else 0,  # current
                item.autoContinue(),  # autocontinue
                item.param1(),  # param1
                item.param2(),  # param2
                item.param3(),  # param3
                item.param4(),  # param4
                item.param5() * (10 ** 7),  # x
                item.param6() * (10 ** 7),  # y
                item.param7() * (10 ** 7)  # z
            )
        else:
            self._mav.mav.mission_item_send(
                self._linkInterface.id(),  # target_system
                190,  # target_component      MAV_COMP_ID_MISSIONPLANNER      190
                missionRequest.seq,  # seq
                item.frame(),  # frame
                item.command(),  # command
                1 if missionRequest.seq == 0 else 0,  # current
                item.autoContinue(),  # autocontinue
                item.param1(),  # param1
                item.param2(),  # param2
                item.param3(),  # param3
                item.param4(),  # param4
                item.param5(),  # x
                item.param6(),  # y
                item.param7()  # z
            )
        self._startAckTimeout(AckType.AckMissionRequest)

    def _handleMissionAck(self, message):  # message type: mavlink_message_t
        missionAck = message
        # Save the retry ack before calling _checkForExpectedAck since we'll need it to determine what type of a
        #       protocol sequence we are in.
        savedExpectedAck = self._expectedAck

        # We can get a MISSION_ACK with an error at any time, so if the Acks don't match it is not a protocol sequence
        #       error. Call _checkForExpectedAck with _retryAck so it will succeed no matter what.
        if not self._checkForExpectedAck(self._expectedAck):
            return

        # qCDebug(MissionManagerLog) << "_handleMissionAck type:"
        #       << _missionResultToString((MAV_MISSION_RESULT)missionAck.type);

        def _handleAckNone():
            # State machine is idle. Vehicle is confused.
            self._sendError(ErrorCode.VehicleError, "Vehicle sent unexpected MISSION_ACK message, error: %s"
                            % self._missionResultToString(missionAck.type))

        def _handleAckMissionCount():
            # MISSION_COUNT message expected
            self._sendError(ErrorCode.VehicleError, "Vehicle returned error: %s."
                            % self._missionResultToString(missionAck.type))
            self._finishTransaction(False)

        def _handleAckMissionItem():
            # MISSION_ITEM expected
            self._sendError(ErrorCode.VehicleError, "Vehicle returned error: %s."
                            % self._missionResultToString(missionAck.type))
            self._finishTransaction(False)

        def _handleAckMissionRequest():
            # MISSION_REQUEST is expected, or MISSION_ACK to end sequence
            if missionAck.type == 0:  # MAV_MISSION_ACCEPTED      0
                if len(self._itemIndicesToWrite) == 0:
                    # qCDebug(MissionManagerLog) << "_handleMissionAck write sequence complete";
                    self._finishTransaction(True)
                else:
                    self._sendError(ErrorCode.MissingRequestsError, "Vehicle did not request all items during write "
                                                                    "sequence, missed count %s."
                                    % self._missionResultToString(missionAck.type))
                    self._finishTransaction(False)
            else:
                self._sendError(ErrorCode.VehicleError, "Vehicle returned error: %s."
                                % self._missionResultToString(missionAck.type))
                self._finishTransaction(False)

        def _handleAckMissionClearAll():
            # MISSION_ACK expected
            if not missionAck.type == 0:  # MAV_MISSION_ACCEPTED      0
                self._sendError(ErrorCode.VehicleError, "Vehicle returned error: %s. Vehicle remove all failed."
                                % self._missionResultToString(missionAck.type))
            self._finishTransaction(missionAck.type == 0)  # MAV_MISSION_ACCEPTED      0

        def _handleAckGuidedItem():
            # MISSION_REQUEST is expected, or MISSION_ACK to end sequence
            if missionAck.type == 0:  # MAV_MISSION_ACCEPTED      0
                # qCDebug(MissionManagerLog) << "_handleMissionAck guided mode item accepted";
                self._finishTransaction(True)
            else:
                self._sendError(ErrorCode.VehicleError, "Vehicle returned error: %s. Vehicle did not accept guided "
                                                        "item." % self._missionResultToString(missionAck.type))
                self._finishTransaction(False)

        def _handleDefault():
            pass

        switcher = {
            AckType.AckNone: _handleAckNone,
            AckType.AckMissionCount: _handleAckMissionCount,
            AckType.AckMissionItem: _handleAckMissionItem,
            AckType.AckMissionRequest: _handleAckMissionRequest,
            AckType.AckMissionClearAll: _handleAckMissionClearAll,
            AckType.AckGuidedItem: _handleAckGuidedItem,
        }
        switcher.get(self._expectedAck, _handleDefault)()

    def _handleMissionCurrent(self, message):  # message type: mavlink_message_t
        missionCurrent = message

        if not missionCurrent.seq == self._currentMissionIndex:
            # qCDebug(MissionManagerLog) << "_handleMissionCurrent currentIndex:" << missionCurrent.seq;
            self._currentMissionIndex = missionCurrent.seq
            self.currentIndexChanged.emit(self._currentMissionIndex)

        if not self._currentMissionIndex == self._lastCurrentIndex:
            # We have to be careful of an RTL sequence causing a change of index to the DO_LAND_START sequence. This
            #   also triggers a flight mode change away from mission flight mode. So we only update _lastCurrentIndex
            #   when the flight mode is mission. But we can run into problems where we may get the MISSION_CURRENT
            #   message for the RTL/DO_LAND_START sequenc change prior to the HEARTBEAT message which contains the
            #   flight mode change which will cause things to work incorrectly. To fix this We force the sequencing of
            #   HEARTBEAT following by MISSION_CURRENT by caching the possible _lastCurrentIndex update until the next
            #   HEARTBEAT comes through.

            # qCDebug(MissionManagerLog) << "_handleMissionCurrent caching _lastCurrentIndex for possible update:"
            #       << _currentMissionIndex;
            self._cachedLastCurrentIndex = self._currentMissionIndex

    def _handleHeartbeat(self, message):  # message type: mavlink_message_t
        # Q_UNUSED(message);

        if self._cachedLastCurrentIndex != -1:
            if self._linkInterface.flightMode() == self._linkInterface.missionFlightMode():
                # qCDebug(MissionManagerLog) << "_handleHeartbeat updating lastCurrentIndex from cached value:"
                #       << _cachedLastCurrentIndex;
                self._lastCurrentIndex = self._cachedLastCurrentIndex
                self._cachedLastCurrentIndex = -1
                self.lastCurrentIndexChanged.emit(self._lastCurrentIndex)

    def _requestNextMissionItem(self):
        if len(self._itemIndicesToRead) == 0:
            self._sendError(ErrorCode.InternalError, "Internal Error: Call to Vehicle _requestNextMissionItem with no "
                                                     "more indices to read")
            return

        # qCDebug(MissionManagerLog) << "_requestNextMissionItem sequenceNumber:retry" << _itemIndicesToRead[0]
        #       << _retryCount;

        if self._linkInterface.supportsMissionItemInt():
            self._mav.mav.mission_request_int_send(
                self._linkInterface.id(),  # target_system
                190,  # target_component      MAV_COMP_ID_MISSIONPLANNER      190
                self._itemIndicesToRead[0]  # seq
            )
        else:
            self._mav.mav.mission_request_send(
                self._linkInterface.id(),  # target_system
                190,  # target_component      MAV_COMP_ID_MISSIONPLANNER      190
                self._itemIndicesToRead[0]  # seq
            )
        self._startAckTimeout(AckType.AckMissionItem)

    def _clearMissionItems(self):
        self._itemIndicesToRead.clear()
        self._clearAndDeleteMissionItems()

    def _sendError(self, errorCode: ErrorCode, errorMsg: str):
        # qCDebug(MissionManagerLog) << "Sending error" << errorCode << errorMsg;
        self.error.emit(errorCode, errorMsg)

    def _ackTypeToString(self, ackType: AckType) -> str:
        switcher = {
            AckType.AckNone: 'No Ack',
            AckType.AckMissionCount: 'MISSION_COUNT',
            AckType.AckMissionItem: 'MISSION_ITEM',
            AckType.AckMissionRequest: 'MISSION_REQUEST',
            AckType.AckGuidedItem: 'Guided Mode Item',
        }
        if ackType not in switcher:
            # qWarning(MissionManagerLog) << "Fell off end of switch statement";
            pass
        return switcher.get(ackType, 'QGC Internal Error')

    def _missionResultToString(self, result) -> str:  # result: type MAV_MISSION_RESULT
        lastRequestString = self._lastMissionReqestString(result)

        switcher = {
            0:      "Mission accepted (MAV_MISSION_ACCEPTED)",
            1:      "Unspecified error (MAV_MISSION_ERROR)",
            2:      "Coordinate frame is not supported (MAV_MISSION_UNSUPPORTED_FRAME)",
            3:      "Command is not supported (MAV_MISSION_UNSUPPORTED)",
            4:      "Mission item exceeds storage space (MAV_MISSION_NO_SPACE)",
            5:      "One of the parameters has an invalid value (MAV_MISSION_INVALID)",
            6:      "Param1 has an invalid value (MAV_MISSION_INVALID_PARAM1)",
            7:      "Param2 has an invalid value (MAV_MISSION_INVALID_PARAM2)",
            8:      "Param3 has an invalid value (MAV_MISSION_INVALID_PARAM3)",
            9:      "Param4 has an invalid value (MAV_MISSION_INVALID_PARAM4)",
            10:     "X/Param5 has an invalid value (MAV_MISSION_INVALID_PARAM5_X)",
            11:     "Y/Param6 has an invalid value (MAV_MISSION_INVALID_PARAM6_Y)",
            12:     "Param7 has an invalid value (MAV_MISSION_INVALID_PARAM7)",
            13:     "Received mission item out of sequence (MAV_MISSION_INVALID_SEQUENCE)",
            14:     "Not accepting any mission commands (MAV_MISSION_DENIED)",
        }
        if result not in switcher:
            # qWarning(MissionManagerLog) << "Fell off end of switch statement";
            pass
        resultString = switcher.get(result, 'QGC Internal Error')

        return resultString + lastRequestString

    def _finishTransaction(self, success: bool):
        self.progressPct.emit(1)

        self._itemIndicesToRead.clear()
        self._itemIndicesToWrite.clear()

        # First thing we do is clear the transaction. This way inProgesss is off when we signal transaction complete.
        currentTransactionType = self._transactionInProgress
        self._transactionInProgress = TransactionType.TransactionNone           # useless
        if currentTransactionType != TransactionType.TransactionNone:
            self._transactionInProgress = TransactionType.TransactionNone
            # qDebug() << "inProgressChanged";
            self.inProgressChanged.emit(False)

        def _handleTransactionRead():
            if not success:
                # Read from vehicle failed, clear partial list
                self._clearAndDeleteMissionItems()
            self.newMissionItemsAvailable.emit(False)

        def _handleTransactionWrite():
            if success:
                # Write succeeded, update internal list to be current
                self._currentMissionIndex = -1
                self._lastCurrentIndex = -1
                self._cachedLastCurrentIndex = -1
                self.currentIndexChanged.emit(-1)
                self.lastCurrentIndexChanged.emit(-1)
                self._clearAndDeleteMissionItems()
                for item in self._writeMissionItems:
                    self._missionItems.append(item)
                self._writeMissionItems.clear()
            else:
                # Write failed, throw out the write list
                self._clearAndDeleteMissionItems()
                self.sendComplete(not success)

        def _handleTransactionRemoveAll():
            self.removeAllComplete(not success)

        switcher = {
            TransactionType.TransactionRead:        _handleTransactionRead,
            TransactionType.TransactionWrite:       _handleTransactionWrite,
            TransactionType.TransactionRemoveAll:   _handleTransactionRemoveAll
        }
        switcher.get(currentTransactionType, lambda: 'nothing')()

        if self._resumeMission:
            self._resumeMission = False
            if success:
                self.resumeMissionReady.emit()
            else:
                self.resumeMissionUploadFail.emit()


    # Internal call to request list of mission items. May be called during a retry sequence.
    def _requestList(self):
        # qCDebug(MissionManagerLog) << "_requestList retry count" << _retryCount;
        self._mav.mav.mission_request_list_send(
            self._linkInterface.id(),           # target_system
            190                                 # target_component      MAV_COMP_ID_MISSIONPLANNER      190
        )
        self._startAckTimeout(AckType.AckMissionCount)

    # This begins the write sequence with the vehicle. This may be called during a retry.
    def _writeMissionCount(self):
        # qCDebug(MissionManagerLog) << "_writeMissionCount count:_retryCount" << _writeMissionItems.count()
        #       << _retryCount;
        self._mav.mav.mission_count_send(
            self._linkInterface.id(),           # target_system
            190,                                # target_component      MAV_COMP_ID_MISSIONPLANNER      190
            len(self._writeMissionItems)        # count
        )
        self._startAckTimeout(AckType.AckMissionRequest)

    def _writeMissionItemsWorker(self):
        self._lastMissionRequest = -1
        self.progressPct.emit(0)

        # qCDebug(MissionManagerLog) << "writeMissionItems count:" << _writeMissionItems.count();

        # Prime write list
        self._itemIndicesToWrite.clear()
        self._itemIndicesToWrite = [i for i in range(len(self._writeMissionItems))]

        self._transactionInProgress = TransactionType.TransactionWrite
        self._retryCount = 0
        self.inProgressChanged(True)
        self._writeMissionCount()

    def _clearAndDeleteMissionItems(self):
        for item in self._missionItems:
            item.deleteLater()
        self._missionItems.clear()

    def _clearAndDeleteWriteMissionItems(self):
        for item in self._writeMissionItems:
            item.deleteLater()
        self._writeMissionItems.clear()

    def _lastMissionReqestString(self, result) -> str:  # result: type MAV_MISSION_RESULT
        if self._lastMissionRequest != -1 and self._lastMissionRequest >= 0 and self._lastMissionRequest < len(self._writeMissionItems):
            item = self._writeMissionItems[self._lastMissionRequest]

            switcher = {
                2:  ". Frame: %d" % item.frame(),               # MAV_MISSION_UNSUPPORTED_FRAME      2
                3:  ". Command: (%d)" % item.command(),         # MAV_MISSION_UNSUPPORTED_FRAME      3
                6:  ". Param1: %f" % item.param1(),             # MAV_MISSION_INVALID_PARAM1         6
                7:  ". Param2: %f" % item.param2(),             # MAV_MISSION_INVALID_PARAM2         7
                8:  ". Param3: %f" % item.param3(),             # MAV_MISSION_INVALID_PARAM3         8
                9:  ". Param4: %f" % item.param4(),             # MAV_MISSION_INVALID_PARAM4         9
                10: ". Param5: %f" % item.param5(),             # MAV_MISSION_INVALID_PARAM5        10
                11: ". Param6: %f" % item.param6(),             # MAV_MISSION_INVALID_PARAM6        11
                12: ". Param7: %f" % item.param7(),             # MAV_MISSION_INVALID_PARAM7        12
                13: ". Sequence: %s" % item.sequenceNumber()    # MAV_MISSION_INVALID_SEQUENCE      13
            }
            return switcher.get(result, '')

    def _removeAllWorker(self):
        # qCDebug(MissionManagerLog) << "_removeAllWorker";

        self.progressPct.emit(0)

        self._mav.mav.mission_clear_all_send(
            self._linkInterface.id(),           # target_system
            190                                 # target_component          MAV_COMP_ID_MISSIONPLANNER      190
        )
        self._startAckTimeout(AckType.AckMissionClearAll)
