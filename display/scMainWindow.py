from PyQt5.QtCore import QUrl, QThread, QSizeF
from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtWebEngineWidgets import QWebEngineView

import sys
import time

class scMap(QWidget):
    def __init__(self, parent=None):
        self.app = QApplication(sys.argv)
        self.browser = QWebEngineView()
        self.initUI()

    def initUI(self):
        self.browser.load(QUrl("file:///map.html"))

        self.browser.show()
        self.app.exec_()

    def runJavaScript(self, js_str):
        self.browser.page().runJavaScript(js_str)

class scMap_t(QThread):
    def __init__(self):
        super().__init__()
        self.app = QApplication(sys.argv)
        self.browser = QWebEngineView()
        self.browser.load(QUrl("file:///map.html"))
        self.browser.setFixedSize(783, 616)
        self.browser.show()

    def run(self):
        self.app.exec_()

    def runJavaScript(self, js_str):
        self.browser.page().runJavaScript(js_str)

    def createMarker(self, name, lat, lng, icon):
        js_str = """%s = new google.maps.Marker({
              position: {lat: %f, lng: %f},
              map: map,
              icon: "data/%s"
          });""" % (name, lat, lng, icon)
        self.runJavaScript(js_str)

    def moveMarker(self, name, lat, lng):
        js_str = """%s.setPosition({lat: %f, lng: %f})""" % (name, lat, lng)
        self.runJavaScript(js_str)

    def deleteMarker(self, name):
        pass

    def setCenter(self, lat, lng):
        js_str = """map.setCenter({lat: %f, lng: %f})""" % (lat, lng)
        self.runJavaScript(js_str)


class UAV():
    def __init__(self, sc_map, name, lat, lng, icon="bluecopter.png"):
        self.map = sc_map
        self.create(name, lat, lng, icon=icon)

    def create(self, name, lat, lng, icon="bluecopter.png"):
        self.name = name
        self.lat = lat
        self.lng = lng
        self.map.createMarker(self.name, self.lat, self.lng, icon)

    def move(self, lat, lng):
        self.lat = lat
        self.lng = lng
        self.map.moveMarker(self.name, self.lat, self.lng)

    def delete(self):
        self.map.deleteMarker(self.name)

def mov(sc_map, lat, lng):


    uav1 = UAV(sc_map, "uav1", lat, lng)
    uav2 = UAV(sc_map, "uav2", lat, lng)
    uav3 = UAV(sc_map, "uav3", lat, lng)
    uav4 = UAV(sc_map, "uav4", lat, lng)

    for i in range(len(l[0])):
        time.sleep(1)
        uav1.move(l[0][i][0], l[0][i][1])
        uav2.move(l[1][i][0], l[1][i][1])
        uav3.move(l[2][i][0], l[2][i][1])
        uav4.move(l[3][i][0], l[3][i][1])


        

if __name__ == '__main__':
    sc_map = scMap_t()

    lat = 39.9651391731
    lng = 116.3420835823

    l = [[(lat, lng)], [(lat, lng)], [(lat, lng)], [(lat, lng)]]
    for i in range(1, 100):
        l[0].append((l[0][i - 1][0] - 0.01, l[0][i - 1][1]))
        l[1].append((l[1][i - 1][0] + 0.01, l[1][i - 1][1]))
        l[2].append((l[2][i - 1][0], l[2][i - 1][1] - 0.01))
        l[3].append((l[3][i - 1][0], l[3][i - 1][1] + 0.01))









    




