from PyQt5.QtWidgets import QApplication

from scMainWindow import scMainWindow
from display.scMapWidget import scMap
from scToolbox import scToolbox



class scApplication(QApplication):
    def __init__(self, List, p_str=None):
        super().__init__(List)

        self.mainWindow = None
        self.sc_map = None
        self.toolbox = None

    def initCommon(self):
        pass

    def initForNormalAppBoot(self):

        self.mainWindow = scMainWindow(self)
        self.sc_map = self.mainWindow.sc_map
        # self.sc_map = scMap(self)
        self.toolbox = scToolbox(self)

    def shutdown(self):
        del self.toolbox
