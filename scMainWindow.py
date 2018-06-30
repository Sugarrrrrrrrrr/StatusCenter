from PyQt5.QtWidgets import QWidget, QApplication, QTabWidget, QHBoxLayout, QVBoxLayout, QGridLayout, QLabel, \
    QPushButton
from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal, Qt
from PyQt5.QtPositioning import QGeoCoordinate
from display.scMapWidget import scMap
from Vehicle import Vehicle
from FirmwarePlugin import ArduCopterFirmwarePlugin
from MissionManager.MissionItem import read_mission_items_file, write_mission_items_file
import sys
from math import radians, cos, sin, asin, sqrt


class scMainWindow(QWidget):
    def __init__(self, app, parent=None):
        super().__init__(parent=parent)
        self._app = app
        self.setWindowTitle('SC')

        self.paraWidgets = QTabWidget(self)
        self.paraWidgets.setFixedSize(214, 616)

        self.sc_map = scMap(self)

        self.layout = QHBoxLayout()
        self.layout.addWidget(self.paraWidgets)
        self.layout.addWidget(self.sc_map)
        self.setLayout(self.layout)

        self.resize(1024, 632)
        self.show()

    def add_para_widget(self, vehicle=None):
        para_widget = ParaWidget(self.paraWidgets, vehicle)
        self.paraWidgets.addTab(para_widget, vehicle.vehicle_name)


class ParaWidget(QWidget):
    def __init__(self, parent=None, vehicle=None):
        super().__init__(parent=parent)
        self.vehicle = vehicle                  # type: Vehicle
        self.m = 8.993216059187306e-06          # about 1m
        self.layout = QVBoxLayout()

        # top
        self.top_widget = QWidget(self)
        self.top_layout = QGridLayout()

        self.label_armed = QLabel('armed:')
        self.top_layout.addWidget(self.label_armed, 0, 0, 1, 1, Qt.AlignBottom)
        self.armed = QLabel('None')
        self.top_layout.addWidget(self.armed, 1, 0, 1, 1, Qt.AlignTop)
        self.label_fight_mode = QLabel('mode:')
        self.top_layout.addWidget(self.label_fight_mode, 0, 1, 1, 1, Qt.AlignBottom)
        self.fight_mode = QLabel('None')
        self.top_layout.addWidget(self.fight_mode, 1, 1, 1, 1, Qt.AlignTop)
        self.label_battery = QLabel('battery:')
        self.top_layout.addWidget(self.label_battery, 0, 2, 1, 1, Qt.AlignBottom)
        self.battery = QLabel('None')
        self.top_layout.addWidget(self.battery, 1, 2, 1, 1, Qt.AlignTop)

        self.label_pitch = QLabel('pitch:')
        self.top_layout.addWidget(self.label_pitch, 2, 0, 1, 1, Qt.AlignBottom)
        self.pitch = QLabel('None')
        self.top_layout.addWidget(self.pitch, 3, 0, 1, 1, Qt.AlignTop)
        self.label_roll = QLabel('roll:')
        self.top_layout.addWidget(self.label_roll, 2, 1, 1, 1, Qt.AlignBottom)
        self.roll = QLabel('None')
        self.top_layout.addWidget(self.roll, 3, 1, 1, 1, Qt.AlignTop)
        self.label_yaw = QLabel('yaw:')
        self.top_layout.addWidget(self.label_yaw, 2, 2, 1, 1, Qt.AlignBottom)
        self.yaw = QLabel('None')
        self.top_layout.addWidget(self.yaw, 3, 2, 1, 1, Qt.AlignTop)

        self.label_lat = QLabel('lat:')
        self.top_layout.addWidget(self.label_lat, 4, 0, 1, 1, Qt.AlignRight)
        self.lat = QLabel('None')
        self.top_layout.addWidget(self.lat, 4, 1, 1, 2, Qt.AlignLeft)
        self.label_lng = QLabel('lng:')
        self.top_layout.addWidget(self.label_lng, 5, 0, 1, 1, Qt.AlignRight)
        self.lng = QLabel('None')
        self.top_layout.addWidget(self.lng, 5, 1, 1, 2, Qt.AlignLeft)
        self.label_alt = QLabel('alt:')
        self.top_layout.addWidget(self.label_alt, 6, 0, 1, 1, Qt.AlignRight)
        self.alt = QLabel('None')
        self.top_layout.addWidget(self.alt, 6, 1, 1, 2, Qt.AlignLeft)

        self.top_widget.setLayout(self.top_layout)

        # bottom
        self.bottom_widget = QWidget(self)
        self.bottom_layout = QGridLayout()

        self.button_armed = QPushButton('解锁', self)
        self.bottom_layout.addWidget(self.button_armed, 0, 0, 1, 1)
        self.button_take_off = QPushButton('起飞', self)
        self.bottom_layout.addWidget(self.button_take_off, 0, 1, 1, 1)
        self.button_landing = QPushButton('降落', self)
        self.bottom_layout.addWidget(self.button_landing, 0, 2, 1, 1)

        self.button_auto = QPushButton('Auto', self)
        self.bottom_layout.addWidget(self.button_auto, 1, 0, 1, 1)
        self.button_guided = QPushButton('Guided', self)
        self.bottom_layout.addWidget(self.button_guided, 1, 1, 1, 1)
        self.button_rtl = QPushButton('RTL', self)
        self.bottom_layout.addWidget(self.button_rtl, 1, 2, 1, 1)

        self.button_forward = QPushButton('N', self)
        self.bottom_layout.addWidget(self.button_forward, 2, 1, 1, 1)
        self.button_left = QPushButton('W', self)
        self.bottom_layout.addWidget(self.button_left, 3, 0, 1, 1)
        self.button_backward = QPushButton('S', self)
        self.bottom_layout.addWidget(self.button_backward, 3, 1, 1, 1)
        self.button_right = QPushButton('E', self)
        self.bottom_layout.addWidget(self.button_right, 3, 2, 1, 1)

        self.button_up = QPushButton('up', self)
        self.bottom_layout.addWidget(self.button_up, 4, 1, 1, 1)
        self.button_down = QPushButton('down', self)
        self.bottom_layout.addWidget(self.button_down, 5, 1, 1, 1)

        self.button_test1 = QPushButton('test1', self)
        self.bottom_layout.addWidget(self.button_test1, 6, 0, 1, 1)
        self.button_test2 = QPushButton('test2', self)
        self.bottom_layout.addWidget(self.button_test2, 6, 1, 1, 1)
        self.button_test3 = QPushButton('test3', self)
        self.bottom_layout.addWidget(self.button_test3, 6, 2, 1, 1)

        self.bottom_widget.setLayout(self.bottom_layout)

        # layout
        self.layout.addWidget(self.top_widget)
        self.layout.addWidget(self.bottom_widget)
        self.setLayout(self.layout)

        if self.vehicle:
            self.signals_dealing()
            self.actions_dealing()
            pass

    def signals_dealing(self):

        @pyqtSlot(int)
        def _handle_armed_changed(armed):
            if armed:
                self.armed.setText('True')
            else:
                self.armed.setText('Flase')
        self.vehicle.armedChanged.connect(_handle_armed_changed)

        @pyqtSlot(str)
        def _handle_flight_mode_changed(flight_mode):
            self.fight_mode.setText(flight_mode)
        self.vehicle.flightModeChanged.connect(_handle_flight_mode_changed)

        @pyqtSlot(int)
        def _handle_battery_remaining_changed(battery_remaining):
            self.battery.setText(str(battery_remaining) + '%')
        self.vehicle.battery_remaining_Changed.connect(_handle_battery_remaining_changed)

        @pyqtSlot(float, float, float)
        def _handle_attitude_changed(pitch, roll, yaw):
            self.pitch.setText(str(pitch))
            self.roll.setText(str(roll))
            self.yaw.setText(str(yaw))
        self.vehicle.attitudeChanged.connect(_handle_attitude_changed)

        @pyqtSlot(str, float, float)
        def _handle_position_changed(vehicle_name, lat, lng):
            self.lat.setText(str(lat))
            self.lng.setText(str(lng))
        self.vehicle.positionChanged.connect(_handle_position_changed)

        @pyqtSlot(float)
        def _handle_alt_changed(alt):
            self.alt.setText(str(alt))
        self.vehicle.altChanged.connect(_handle_alt_changed)

    def actions_dealing(self):
        @pyqtSlot()
        def _handle_button_armed_clicked():
            # self.vehicle.setArmed(True)
            if not self.vehicle.firmwarePlugin()._armVehicleAndValidate(self.vehicle):
                print('setArmed fail')
        self.button_armed.clicked.connect(_handle_button_armed_clicked)

        @pyqtSlot()
        def _handle_button_take_off_clicked():
            firmwarePlugin = self.vehicle.firmwarePlugin()          # type: ArduCopterFirmwarePlugin
            firmwarePlugin.guidedModeTakeoff(self.vehicle)
        self.button_take_off.clicked.connect(_handle_button_take_off_clicked)

        @pyqtSlot()
        def _handle_button_landing_clicked():
            firmwarePlugin = self.vehicle.firmwarePlugin()  # type: ArduCopterFirmwarePlugin
            firmwarePlugin.guidedModeLand(self.vehicle)
        self.button_landing.clicked.connect(_handle_button_landing_clicked)

        @pyqtSlot()
        def _handle_button_auto_clicked():
            firmwarePlugin = self.vehicle.firmwarePlugin()  # type: ArduCopterFirmwarePlugin
            firmwarePlugin._setFlightModeAndValidate(self.vehicle, firmwarePlugin.missionFlightMode())
        self.button_auto.clicked.connect(_handle_button_auto_clicked)

        @pyqtSlot()
        def _handle_button_guided_clicked():
            firmwarePlugin = self.vehicle.firmwarePlugin()  # type: ArduCopterFirmwarePlugin
            firmwarePlugin.setGuidedMode(self.vehicle, True)
        self.button_guided.clicked.connect(_handle_button_guided_clicked)

        @pyqtSlot()
        def _handle_button_rtl_clicked():
            firmwarePlugin = self.vehicle.firmwarePlugin()  # type: ArduCopterFirmwarePlugin
            firmwarePlugin.guidedModeRTL(self.vehicle)
        self.button_rtl.clicked.connect(_handle_button_rtl_clicked)

        @pyqtSlot()
        def _handle_button_forward_clicked():
            if self.vehicle.lat is None or self.vehicle.lng is None or \
                    (self.vehicle.lat == 0 and self.vehicle.lng == 0):
                print('can not get current position')
                return
            gotoCoord = QGeoCoordinate(self.vehicle.lat + 5 * self.m, self.vehicle.lng, 5)
            firmwarePlugin = self.vehicle.firmwarePlugin()  # type: ArduCopterFirmwarePlugin
            firmwarePlugin.guidedModeGotoLocation(self.vehicle, gotoCoord)
        self.button_forward.clicked.connect(_handle_button_forward_clicked)

        @pyqtSlot()
        def _handle_button_left_clicked():
            if self.vehicle.lat is None or self.vehicle.lng is None or \
                    (self.vehicle.lat == 0 and self.vehicle.lng == 0):
                print('can not get current position')
                return
            gotoCoord = QGeoCoordinate(self.vehicle.lat, self.vehicle.lng - 5 * self.m, 5)
            firmwarePlugin = self.vehicle.firmwarePlugin()  # type: ArduCopterFirmwarePlugin
            firmwarePlugin.guidedModeGotoLocation(self.vehicle, gotoCoord)
        self.button_left.clicked.connect(_handle_button_left_clicked)

        @pyqtSlot()
        def _handle_button_right_clicked():
            if self.vehicle.lat is None or self.vehicle.lng is None or \
                    (self.vehicle.lat == 0 and self.vehicle.lng == 0):
                print('can not get current position')
                return
            gotoCoord = QGeoCoordinate(self.vehicle.lat, self.vehicle.lng + 5 * self.m, 5)
            firmwarePlugin = self.vehicle.firmwarePlugin()  # type: ArduCopterFirmwarePlugin
            firmwarePlugin.guidedModeGotoLocation(self.vehicle, gotoCoord)
        self.button_right.clicked.connect(_handle_button_right_clicked)

        @pyqtSlot()
        def _handle_button_backward_clicked():
            if self.vehicle.lat is None or self.vehicle.lng is None or \
                    (self.vehicle.lat == 0 and self.vehicle.lng == 0):
                print('can not get current position')
                return
            gotoCoord = QGeoCoordinate(self.vehicle.lat - 5 * self.m, self.vehicle.lng, 5)
            firmwarePlugin = self.vehicle.firmwarePlugin()  # type: ArduCopterFirmwarePlugin
            firmwarePlugin.guidedModeGotoLocation(self.vehicle, gotoCoord)
        self.button_backward.clicked.connect(_handle_button_backward_clicked)

        @pyqtSlot()
        def _handle_button_up_clicked():
            firmwarePlugin = self.vehicle.firmwarePlugin()  # type: ArduCopterFirmwarePlugin
            firmwarePlugin.guidedModeChangeAltitude(self.vehicle, 1.5)
        self.button_up.clicked.connect(_handle_button_up_clicked)

        @pyqtSlot()
        def _handle_button_down_clicked():
            firmwarePlugin = self.vehicle.firmwarePlugin()  # type: ArduCopterFirmwarePlugin
            firmwarePlugin.guidedModeChangeAltitude(self.vehicle, -1.5)
        self.button_down.clicked.connect(_handle_button_down_clicked)

        @pyqtSlot()
        def _handle_button_test1_clicked():
            print('button_test1_clicked')
            l = read_mission_items_file('C:/Users/ZhangYS/Desktop/auto_3.waypoints')
            self.vehicle.missionManager().writeMissionItems(l)
        self.button_test1.clicked.connect(_handle_button_test1_clicked)

        @pyqtSlot()
        def _handle_button_test2_clicked():
            print('button_test2_clicked')
            print(self.vehicle.missionManager()._missionItems)
        self.button_test2.clicked.connect(_handle_button_test2_clicked)

        @pyqtSlot()
        def _handle_button_test3_clicked():
            print('button_test3_clicked')
            l = []
            write_mission_items_file(l, 'C:/Users/ZhangYS/Desktop/waypoints_file_write.txt')
        self.button_test3.clicked.connect(_handle_button_test3_clicked)

class test(QObject):
    def __init__(self):
        super().__init__()
        self.vehicle_name = 'uav_default'

    armedChanged = pyqtSignal(int)
    flightModeChanged = pyqtSignal(str)
    positionChanged = pyqtSignal(str, float, float)
    altChanged = pyqtSignal(float)
    battery_remaining_Changed = pyqtSignal(int)
    attitudeChanged = pyqtSignal(float, float, float)


def haversine(lon1, lat1, lon2, lat2):  # 经度1，纬度1，经度2，纬度2 （十进制度数）
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    """
    # 将十进制度数转化为弧度
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine公式
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    r = 6371  # 地球平均半径，单位为公里
    return c * r * 1000

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWindow = scMainWindow(None)
    # mainWindow.resize(1024, 632)
    # mainWindow.show()

    vehicle = test()
    mainWindow.add_para_widget(vehicle)

    vehicle.armedChanged.emit(0)
    vehicle.flightModeChanged.emit('Auto')
    vehicle.battery_remaining_Changed.emit(50)
    vehicle.attitudeChanged.emit(9.9, 9.9, 9.9)
    vehicle.positionChanged.emit('uav_2', 111, 222)
    vehicle.altChanged.emit(333)

    app.exec()
