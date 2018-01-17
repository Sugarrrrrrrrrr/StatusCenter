from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QMessageBox, QDialog


class bridge(QObject):
    def __init__(self):
        super().__init__()

    def instance(self):
        return bridge()

    def showMsgBox(self):
        QMessageBox.aboutQt(None, 0, 'Qt')

class Dialog(QDialog):
    def __init__(self):
        pass
