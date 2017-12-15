from PyQt5.QtWidgets import QApplication

from display.scMainWindow import scMap
from scToolbox import scToolbox


class scApplication(QApplication):
    def __init__(self, List, p_str=None):
        super().__init__(List)
        self.toolbox = scToolbox(self)

    def initCommon(self):
        pass

    def initForNormalAppBoot(self):
        self.sc_map = scMap()

    def shutdown(self):
        del self.toolbox
