import sys
import logging
import traceback

from PyQt4 import QtGui

from n810roomba import common
from n810roomba.ui.mainwindow import MainWindow


log = logging.getLogger('guiclient')


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)

    client = common.RoombaClient()
    try:
        client.connect()
    except Exception, ex:
        traceback.print_exc()

    win = MainWindow(client.bot)
    win.show()
    status = app.exec_()
    #win.exit_cleanup()
    sys.exit(status)

