from PyQt5.QtCore import QObject, pyqtSignal
from websockettransport import WebSocketTransport


class WebSocketClientWrapper(QObject):
    clientConnected = pyqtSignal(object)

    def __init__(self, server, parent=None):
        super().__init__(parent)
        self.m_server = server
        server.newConnection.connect(self.handleNewConnection)

    def handleNewConnection(self):
        self.clientConnected.emit(WebSocketTransport(self.m_server.nextPendingConnection()))
