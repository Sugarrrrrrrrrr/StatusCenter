from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot


class Bridge(QObject):
    def __init__(self):
        super().__init__()

    signal_test = pyqtSignal()
    positionChanged = pyqtSignal(str, float, float)

    def __init__(self, parent=None):
        super().__init__(parent)

    @pyqtSlot()
    def slot_test(self):
        print('slot_test')

    @pyqtSlot(str, float, float)
    def positionChanged_test(self, s, f1, f2):
        print(s, f1, f2)
