from PyQt5.QtWidgets import QApplication

from display.scMainWindow import scMap
from scToolbox import scToolbox


class scApplication(QApplication):
    def __init__(self, List, p_str=None):
        super().__init__(List)

        self.sc_map = None
        self.toolbox = None

    def initCommon(self):
        pass

    def initForNormalAppBoot(self):

        self.toolbox = scToolbox(self)
        self.sc_map = scMap(self)

    def shutdown(self):
        del self.toolbox
