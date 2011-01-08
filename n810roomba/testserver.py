import Pyro.naming
import Pyro.core
from Pyro.errors import PyroError,NamingError

import pyrobot

import settings



class RoombaFacade(Pyro.core.ObjBase):
    def __init__(self, pyro_daemon, *args, **kwargs):
        self.daemon = pyro_daemon
        super(RoombaFacade, self).__init__(*args, **kwargs)

    def make_roomba(self, pyro_name, *args, **kwargs):
        bot = pyrobot.Roomba(*args, **kwargs)
        self.daemon.connect(bot, pyro_name)
        return bot


def main():
    Pyro.core.initServer()
    daemon = Pyro.core.Daemon()
    # locate the NS
    locator = Pyro.naming.NameServerLocator()
    print 'searching for Name Server...'
    ns = locator.getNS()
    daemon.useNameServer(ns)

    try:
        ns.unregister(settings.PYRO_FACADE_NAME)
    except NamingError:
        pass

    daemon.connect(RoombaFacade(), settings.FACADE_NAME)

    # enter the server loop.
    print 'Server object "test" ready.'
    daemon.requestLoop()

if __name__=="__main__":
    main()
