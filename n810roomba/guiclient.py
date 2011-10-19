import sys
import logging

from PyQt4 import QtGui

from n810roomba.ui.mainwindow import MainWindow

from n810roomba.client import LocalBot, RemoteClient


log = logging.getLogger(__name__)


class Dummy(object):
    def __getattr__(self, key):
        return self

    def __call__(self, *args, **kwargs):
        return self

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)

    client = RemoteClient()
    try:
        client.connect()
    except Exception, ex:
        #traceback.print_exc()
        pass

    if client.bot:
        client.bot.Control()
    else:
        client.bot = Dummy()
        log.critical('Could not connect to roomba. runnin offline')
        client.bot = LocalBot()
    win = MainWindow(client.bot)
    win.show()
    status = app.exec_()
    #win.exit_cleanup()
    win.finish()
    sys.exit(status)

