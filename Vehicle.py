from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot


class Vehicle(QObject):
    def __init__(self, app, link, parent=None):
        super().__init__(parent=parent)
        self._app = app
        self._link = link

        self._firmwareType = 3                      # MAV_AUTOPILOT_ARDUPILOTMEGA       3
        self._supportsMissionItemInt = False

    def __del__(self):
        pass

    def id(self):
        return 1

    def defaultComponentId(self):
        return 1

    def apmFirmware(self):
        return self._firmwareType == 3              # MAV_AUTOPILOT_ARDUPILOTMEGA       3

    def px4Firmware(self):
        return self._firmwareType == 12             # MAV_AUTOPILOT_PX4                 12

    def genericFirmware(self):
        return not self.apmFirmware() and not self.px4Firmware()

    def setHomePosition(self, x, y, z):
        pass

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

    def flightMode(self):
        return 1

    def missionFlightMode(self):
        return 1

    def supportsMissionItemInt(self):
        return self._supportsMissionItemInt
