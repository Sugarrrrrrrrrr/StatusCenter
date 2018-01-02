from PyQt5.QtCore import QObject
from comm.LinkInterface import LinkInterface

import json


class scToolbox(QObject):
    def __init__(self, app, parent=None):
        super().__init__(parent=parent)
        self.parent = parent
        self.app = app

        if not self.parent:
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



