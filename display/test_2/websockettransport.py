from PyQt5.QtWebChannel import QWebChannelAbstractTransport
from PyQt5.QtCore import QJsonDocument, QJsonParseError


class WebSocketTransport(QWebChannelAbstractTransport):
    def __init__(self, socket):
        super().__init__(socket)
        self.m_socket = socket
        socket.textMessageReceived.connect(self.textMessageReceived)
        socket.disconnected.connect(self.deleteLater)

    def __del__(self):
        self.m_socket.deleteLater()

    def sendMessage(self, message):
        doc = QJsonDocument(message)
        self.m_socket.sendTextMessage(doc.toJson().data().decode('utf-8'))

    def textMessageReceived(self, messageData):
        error = QJsonParseError()
        message = QJsonDocument(eval(messageData))

        '''
        if error:
            print("Failed to parse text message as JSON object:", messageData)
            print("Error is:", error.errorString())
            return
        elif not messageData.isObject():
            print("Received JSON message that is not an object: ", messageData)
            return
        '''
        
        self.messageReceived.emit(message.object(), self)



if __name__ == '__main__':
    pass
