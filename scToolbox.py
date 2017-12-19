from PyQt5.QtCore import QObject
from comm.LinkInterface import LinkInterface

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

        self.links_name = []
        self.links = []
        self.home_create = False
        self.home_lat = 39.9651391731
        self.home_lng = 116.3420835823

        self.update_links_name()

        for link_name in self.links_name:
            link = LinkInterface(link_name, self.app, self)
            self.links.append(link)

    def update_links_name(self):
        with open('.config', 'r') as file:
            for line in file:
                if not line.startswith('#'):
                    line_list = line.strip().replace(' ', '').split(',')
                    self.links_name.append(':'.join(line_list))

    def set_home(self, lat, lng):
        self.home_create = True
        self.home_lat = lat
        self.home_lng = lng
        self.app.sc_map.set_home(self.home_lat, self.home_lng)
        self.app.sc_map.setCenter(self.home_lat, self.home_lng)



