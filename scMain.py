
from scApplication import scApplication
from PyQt5.QtWidgets import QApplication

import sys


if __name__ == '__main__':
    app = scApplication(sys.argv)
    app.initCommon()

    exitCode = 0

    if not app.initForNormalAppBoot():
        exitCode = app.exec_()

    app.shutdown()
    del app
    exit(exitCode)
