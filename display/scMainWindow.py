from PyQt5.QtCore import QUrl, QThread
from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtWebEngineWidgets import QWebEngineView

import sys

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
        

if __name__ == '__main__':
    sc_map = scMap_t()

    lat = -25.363
    lng = 131.044

    




