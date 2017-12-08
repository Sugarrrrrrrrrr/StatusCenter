# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'dialog.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets, QtWebSockets, QtNetwork, QtWebChannel
from websocketclientwrapper import WebSocketClientWrapper
import sys


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(400, 300)
        self.gridLayout = QtWidgets.QGridLayout(Dialog)
        self.gridLayout.setObjectName("gridLayout")
        self.input = QtWidgets.QLineEdit(Dialog)
        self.input.setObjectName("input")
        self.gridLayout.addWidget(self.input, 1, 0, 1, 1)
        self.send = QtWidgets.QPushButton(Dialog)
        self.send.setObjectName("send")
        self.gridLayout.addWidget(self.send, 1, 1, 1, 1)
        self.output = QtWidgets.QPlainTextEdit(Dialog)
        self.output.setReadOnly(True)
        self.output.setPlainText("Initializing WebChannel...")
        self.output.setBackgroundVisible(False)
        self.output.setObjectName("output")
        self.gridLayout.addWidget(self.output, 0, 0, 1, 2)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.input.setPlaceholderText(_translate("Dialog", "Message Contents"))
        self.send.setText(_translate("Dialog", "Send"))

class Core(QtCore.QObject):
    sendText = QtCore.pyqtSignal(str)

    def __init__(self, dialog, parent = None):
        super().__init__(parent)
        self.dialog = dialog
        dialog.sendText.connect(self.sendText)

    @QtCore.pyqtSlot(str)
    def receiveText(self, text):
        self.dialog.displayMessage("Received message: " + text)


class Dialog(QtWidgets.QDialog):
    sendText = QtCore.pyqtSignal(str)
    clicked = QtCore.pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.ui.send.clicked.connect(self.clicked)

    def displayMessage(self, message):
        self.ui.output.appendPlainText(message)

    def clicked(self):
        text = self.ui.input.text()
        if not text:
            return
        self.sendText.emit(text)
        self.displayMessage("Sent message: "+text)
        self.ui.input.clear()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    server = QtWebSockets.QWebSocketServer("QWebChannel Standalone Example Server", QtWebSockets.QWebSocketServer.NonSecureMode)
    if not server.listen(QtNetwork.QHostAddress.LocalHost, 12345):
        print("Failed to open web socket server.")

    clientWrapper = WebSocketClientWrapper(server)

    channel = QtWebChannel.QWebChannel()
    clientWrapper.clientConnected.connect(channel.connectTo)

    dialog = Dialog(None)

    core = Core(dialog)
    channel.registerObject("core", core)

    url_string = "file:///test.html"
    url = QtCore.QUrl(url_string)
    b = QtGui.QDesktopServices.openUrl(url)
    print(b)

    dialog.displayMessage("Initialization complete, opening browser at %s." % url.toDisplayString())
    dialog.show()

    app.exec_()


