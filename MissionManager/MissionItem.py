from PyQt5.QtCore import QObject

class MissionItem(QObject):
    def __init__(self, item=None, parent=None):
        super().__init__(parent=parent)
        self.parent = parent
        self.item_recieved = None
        self._doJumpId = -1

        self._sequenceNumber = 0
        self._isCurrentItem = 0
        self._frame = 0
        self._command = 0
        self._param1 = 0.0
        self._param2 = 0.0
        self._param3 = 0.0
        self._param4 = 0.0
        self._param5 = 0.0
        self._param6 = 0.0
        self._param7 = 0.0
        self._autoContinue = 0
        if item is not None:
            self.load(item)

    def load(self, item):
        self.item_recieved = item
        if isinstance(self.item_recieved, str):
            params = self.item_recieved.strip().split('\t')
            if len(params) == 12:
                self.setSequenceNumber(eval(params[0]))
                self.setIsCurrentItem(eval(params[1]))
                self.setFrame(eval(params[2]))
                self.setCommand(eval(params[3]))
                self.setParam1(eval(params[4]))
                self.setParam2(eval(params[5]))
                self.setParam3(eval(params[6]))
                self.setParam4(eval(params[7]))
                self.setParam5(eval(params[8]))
                self.setParam6(eval(params[9]))
                self.setParam7(eval(params[10]))
                self.setAutoContinue(eval(params[11]))
                return True
            print('error: wrong len of item: ', len(params))
            return False
        else:
            pass
        print('error: unknow item type: ', type(self.item_recieved))
        return False

    def sequenceNumber(self):
        return self._sequenceNumber

    def setSequenceNumber(self, sequenceNumber):
        if self._sequenceNumber != sequenceNumber:
            self._sequenceNumber = sequenceNumber
            # emit emit sequenceNumberChanged(int)

    def isCurrentItem(self):
        if self._isCurrentItem:
            return True
        else:
            return False

    def setIsCurrentItem(self, isCurrentItem):
        if self._isCurrentItem != isCurrentItem:
            self._isCurrentItem = isCurrentItem
            # emit isCurrentItemChanged(bool)

    def frame(self):
        return self._frame

    def setFrame(self, frame):
        if self._frame != frame:
            self._frame = frame

    def command(self):
        return self._command

    def setCommand(self, command):
        if self._command != command:
            self._command = command

    def param1(self):
        return self._param1

    def setParam1(self, param):
        if self._param1 != param:
            self._param1 = float(param)

    def param2(self):
        return self._param2

    def setParam2(self, param):
        if self._param2 != param:
            self._param2 = float(param)

    def param3(self):
        return self._param3

    def setParam3(self, param):
        if self._param3 != param:
            self._param3 = float(param)

    def param4(self):
        return self._param4

    def setParam4(self, param):
        if self._param4 != param:
            self._param4 = float(param)

    def param5(self):
        return self._param5

    def setParam5(self, param):
        if self._param5 != param:
            self._param5 = float(param)

    def param6(self):
        return self._param6

    def setParam6(self, param):
        if self._param6 != param:
            self._param6 = float(param)

    def param7(self):
        return self._param7

    def setParam7(self, param):
        if self._param7 != param:
            self._param7 = float(param)

    def autoContinue(self):
        if self._autoContinue:
            return True
        else:
            return False

    def setAutoContinue(self, autoContinue):
        if self._autoContinue != autoContinue:
            self._autoContinue = autoContinue

    def specifiedFlightSpeed(self):
        flightSpeed = None
        # command MAV_CMD_DO_CHANGE_SPEED 178
        if self._command == 178 and self._param2 > 0:
            flightSpeed = self._param2
        return flightSpeed

    def _param2Changed(self):
        # value
        flightSpeed = self.specifiedFlightSpeed()
        if flightSpeed is not None:
            # emit specifiedFlightSpeedChanged(flightSpeed)
            pass


def read_mission_items_file(file_name):
    mission_items = []
    with open(file_name, 'r') as file:
        file.readline()
        for line in file:
            mission_item = MissionItem(line)
            mission_items.append(mission_item)
    return mission_items


def write_mission_items_file(mission_items, file_name):
    first_line = 'QGC WPL 110\n'
    with open(file_name, 'w') as file:
        file.write(first_line)
        for mission_item in mission_items:
            if mission_item.isCurrentItem():
                isCurrentItem = 1
            else:
                isCurrentItem = 0

            if mission_item.autoContinue():
                autoContinue = 1
            else:
                autoContinue = 0

            line = '%d\t%d\t%d\t%d\t%f\t%f\t%f\t%f\t%f\t%f\t%f\t%d\n' % (
                mission_item.sequenceNumber(),
                isCurrentItem,
                mission_item.frame(),
                mission_item.command(),
                mission_item.param1(),
                mission_item.param2(),
                mission_item.param3(),
                mission_item.param4(),
                mission_item.param5(),
                mission_item.param6(),
                mission_item.param7(),
                autoContinue
            )
            file.write(line)


if __name__ == '__main__':
    l = read_mission_items_file('waypoints_file.waypoints')
    write_mission_items_file(l, 'waypoints_file_write.waypoints')
    print(l)







