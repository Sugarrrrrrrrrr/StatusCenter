from PyQt5.QtCore import QUrl, QThread, QSizeF
from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtWebEngineWidgets import QWebEngineView

import sys
import time
import threading

class scMap(QWidget):
    # map class used
    def __init__(self, app, parent=None):
        super().__init__(parent=parent)
        self.app = app
        self.browser = QWebEngineView(self)
        self.initUI()

        self.bool_zoom_change = True
        self.bool_reset_map = True
        self.zoom_got = None
        self.bounds_got = None

        self.bool_contains = None
        self.bool_contains_1 = None
        self.bool_contains_2 = None

    def initUI(self):
        self.browser.load(QUrl("file:///display/map.html"))
        self.browser.setFixedSize(783, 616)
        self.show()

    def runJavaScript(self, js_str):
        self.browser.page().runJavaScript(js_str)

    def runJavaScript_with_callback(self, js_str, callback):
        self.browser.page().runJavaScript(js_str, callback)

    def createMarker(self, name, lat, lng, icon):
        js_str = """%s = new google.maps.Marker({
              position: {lat: %f, lng: %f},
              map: map,
              icon: "data/%s"
          });""" % (name, lat, lng, icon)
        self.runJavaScript(js_str)

    def moveMarker(self, name, lat, lng, link):

        # 判断是否越界，越界则重置地图中心与缩放
        if self.cross_the_border(lat, lng, link):
            # print('cross_the_border')
            self.reset_map(link)

        js_str = """%s.setPosition({lat: %f, lng: %f})""" % (name, lat, lng)
        self.runJavaScript(js_str)

    def deleteMarker(self, name):
        pass

    def setCenter(self, lat, lng):
        js_str = """map.setCenter({lat: %f, lng: %f})""" % (lat, lng)
        self.runJavaScript(js_str)

    def panTo(self, lat, lng):
        js_str = """map.panTo({lat: %f, lng: %f})""" % (lat, lng)
        self.runJavaScript(js_str)

    def set_home(self, lat, lng):
        js_str = """home = new google.maps.Marker({
                    position: {lat: %f, lng: %f},
                    map: map,
                    icon: "data/home.png"
                });""" % (lat, lng)
        self.runJavaScript(js_str)

    def cross_the_border(self, lat, lng, link):
        # None for no result

        js_str = "map.getBounds().contains({lat: %f, lng: %f})" % (lat, lng)
        self.runJavaScript_with_callback(js_str, link.js_callback)

        bool_ctb = link.js_result
        link.js_result = None
        if bool_ctb is None:
            return bool_ctb
        else:
            return not bool_ctb

    def cross_the_border_1(self, lat, lng):
        # None for no result
        js_str = "map.getBounds().contains({lat: %f, lng: %f})" % (lat, lng)
        self.runJavaScript_with_callback(js_str, self.ctb_callback_1)

        bool_ctb = self.bool_contains_1
        self.bool_contains_1 = None
        if bool_ctb is None:
            return bool_ctb
        else:
            return not bool_ctb

    def cross_the_border_2(self, lat, lng):
        # None for no result
        js_str = "map.getBounds().contains({lat: %f, lng: %f})" % (lat, lng)
        self.runJavaScript_with_callback(js_str, self.ctb_callback_2)

        bool_ctb = self.bool_contains_2
        self.bool_contains_2 = None
        if bool_ctb is None:
            return bool_ctb
        else:
            return not bool_ctb

    def ctb_callback(self, result):
        self.bool_contains = result

    def ctb_callback_1(self, result):
        self.bool_contains_1 = result

    def ctb_callback_2(self, result):
        self.bool_contains_2 = result

    def reset_map(self, link):
        if self.bool_reset_map:
            self.bool_reset_map = False

            lat1 = None
            lat2 = None
            lng1 = None
            lng2 = None

            for linkInt in self.app.toolbox.linkMgr.links:
                if lat1 is None or linkInt.uav_lat < lat1:
                    lat1 = linkInt.uav_lat
                if lat2 is None or linkInt.uav_lat > lat2:
                    lat2 = linkInt.uav_lat
                if lng1 is None or linkInt.uav_lng < lng1:
                    lng1 = linkInt.uav_lng
                if lng2 is None or linkInt.uav_lng > lng2:
                    lng2 = linkInt.uav_lng

            self.panTo((lat1 + lat2) / 2, (lng1 + lng2) / 2)

            # 预留范围
            p = 1/8
            lat1_goal = lat1 - (lat2 - lat1) * p
            lat2_goal = lat2 + (lat2 - lat1) * p
            lng1_goal = lng1 - (lng2 - lng1) * p
            lng2_goal = lng2 + (lng2 - lng1) * p

            # get map bounds (lat1_got, lat2_got, lng1_got, lng2_got)
            bounds = None
            while bounds is None:
                bounds = self.getBounds()
            lat1_got, lat2_got, lng1_got, lng2_got = bounds
            # get zoom(n_got)
            n_got = None
            while n_got is None:
                n_got = self.getZoom()
            # compare (lat1_goal, lat2_goal, lng1_goal, lng2_goal) and (lat1_got, lat2_got, lng1_got, lng2_got)
            ratio = max(
                ([(lat2_goal - lat1_goal) / (lat2_got - lat1_got), (lng2_goal - lng1_goal) / (lng2_got - lng1_got)]))
            # confirm delta
            delta = 0
            if ratio > 1:
                # while ratio > 1:
                #    delta -= 1
                #    ratio /= 2
                delta = -1
            elif 1 / 2 >= ratio > 0:
                # while ratio <= 1 / 2:
                #   delta += 1
                #   ratio *= 2
                 delta = 1
            elif ratio == 0 or 1 >= ratio > 1 / 2:
                pass
            else:
                input('reset map::ratio error')

            n_goal = n_got + delta
            if n_goal > 20:
                n_goal = 20
            elif n_goal < 3:
                n_goal = 3

            #if delta != 0:
            #    print(threading.current_thread().getName(), 'delta:', delta, '|', 'n_goal:', n_goal)
            #    print((lat1_goal, lat2_goal, lng1_goal, lng2_goal), (lat1_got, lat2_got, lng1_got, lng2_got))

            # self.zoom_change(zoom=n_goal)
            self.fitBounds(lat1_goal, lat2_goal, lng1_goal, lng2_goal)

            self.bool_reset_map = True

    def fitBounds(self, lat1_goal, lat2_goal, lng1_goal, lng2_goal):
        js_str = '''fitBounds(%f, %f, %f, %f)''' % (lat1_goal, lat2_goal, lng1_goal, lng2_goal)
        self.runJavaScript(js_str)

    def zoom_change(self, delta=-1, zoom=None):
        if self.bool_zoom_change:
            self.bool_zoom_change = False

            if zoom is None:
                n_got = None
                while n_got is None:
                    n_got = self.getZoom()

                n_goal = n_got + delta
                if n_goal > 20:
                    n_goal = 20
                elif n_goal < 3:
                    n_goal = 3

                if delta != 0:
                    print('n_goal:', n_goal, threading.current_thread().getName())

                while n_got != n_goal:
                    # setZoom
                    js_str = '''map.setZoom(%d)''' % n_goal
                    self.runJavaScript(js_str)
                    # getZoom
                    n_temp = None
                    while n_temp is None:
                        n_temp = self.getZoom()
                    n_got = n_temp
            else:
                n_got = None
                while n_got is None:
                    n_got = self.getZoom()

                n_goal = zoom
                while n_got != n_goal:
                    # setZoom
                    js_str = '''map.setZoom(%d)''' % n_goal
                    self.runJavaScript(js_str)
                    # getZoom
                    n_temp = None
                    while n_temp is None:
                        n_temp = self.getZoom()
                    n_got = n_temp

        self.bool_zoom_change = True

    def getZoom(self):
        js_str = '''map.getZoom()'''
        self.runJavaScript_with_callback(js_str, self.callback_getZoom)
        zoom = self.zoom_got
        self.zoom_got = None
        return zoom

    def callback_getZoom(self, result):
        self.zoom_got = result

    def getBounds(self):
        js_str = '''map.getBounds()'''
        self.runJavaScript_with_callback(js_str, self.callback_getBounds)
        bounds = self.bounds_got
        self.bounds_got = None
        if bounds is None:
            return bounds
        else:
            # return (lat1_got, lat2_got, lng1_got, lng2_got)
            return(bounds['f']['b'], bounds['f']['f'], bounds['b']['b'], bounds['b']['f'])

    def callback_getBounds(self, result):
        self.bounds_got = result

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









    




