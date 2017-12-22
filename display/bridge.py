from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot


class Bridge(QObject):

    signal_test = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

    @pyqtSlot()
    def slot_test(self):
        print('slot_test')