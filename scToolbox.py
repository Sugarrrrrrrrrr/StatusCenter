from PyQt5.QtCore import QObject


class scToolbox(QObject):
    def __init__(self, app, parent=None):
        super().__init__(parent=parent)
        self.app = app

