import sys

from PyQt4 import QtGui

from n810roomba.ui.mainwindow import MainWindow

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)

    win = MainWindow()
    win.show()
    status = app.exec_()
    #win.exit_cleanup()
    sys.exit(status)

