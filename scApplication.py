from PyQt5.QtWidgets import QApplication

from scMainWindow import scMainWindow
from display.scMapWidget import scMap
from scToolbox import scToolbox



class scApplication(QApplication):
    def __init__(self, List, p_str=None):
        super().__init__(List)
        self._app = self

        self.mainWindow = None
        self.sc_map = None
        self.toolbox = None

# public
    # Although public, these methods are internal and should only be called by UnitTest code

    # @brief Perform initialize which is common to both normal application running and unit tests.
    #       Although public should only be called by main.
    def initCommon(self):
        pass

    # @brief Initialize the application for normal application boot. Or in other words we are not going to run unit
    #   tests.
    #       Although public should only be called by main.
    def initForNormalAppBoot(self):
        self.mainWindow = scMainWindow(self)
        self.sc_map = self.mainWindow.sc_map
        # self.sc_map = scMap(self)
        self.toolbox = scToolbox(self)

    # Shutdown the application object
    def shutdown(self):
        del self.toolbox

    # @brief Returns the QGCApplication object singleton.
    def scApp(self):
        return self._app
