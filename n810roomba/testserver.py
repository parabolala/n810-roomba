import optparse

import Pyro.naming
import Pyro.core
from Pyro.errors import PyroError, NamingError

from pyro_facade import RoombaFacade

import settings

parser = optparse.OptionParser(description='Roomba n810 some bla-bla')
parser.add_option('-H', '--host', dest='host', action='store',
                   default=None,
                   help='the hostname that the daemon will use when publishing URIs')

opts, args = parser.parse_args()

daemon = None

def main():
    global daemon
    Pyro.core.initServer()
    daemon = Pyro.core.Daemon(publishhost=opts.host)
    # locate the NS
    locator = Pyro.naming.NameServerLocator()
    print 'searching for Name Server...'
    ns = locator.getNS()
    daemon.useNameServer(ns)

    try:
        ns.unregister(settings.PYRO_FACADE_NAME)
    except NamingError:
        pass

    obj = RoombaFacade(daemon)

    daemon.connect(RoombaFacade(daemon), settings.PYRO_FACADE_NAME)

    # enter the server loop.
    print 'Server object "test" ready.'
    daemon.requestLoop()

if __name__=="__main__":
    main()
