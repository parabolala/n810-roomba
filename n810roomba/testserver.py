import optparse
import logging

# import this before Pyro to override PYRO_CONFIG_FILE
from n810roomba import settings

import Pyro.naming
from Pyro.errors import NamingError

from n810roomba.pyro_facade import RoombaFacade


parser = optparse.OptionParser(description='Roomba n810 some bla-bla')
parser.add_option('-H', '--my-host', dest='host', action='store',
                   default=None,
                   help='the hostname that the daemon will use when publishing URIs')

log = logging.getLogger('server')

def main():
    opts, args = parser.parse_args()

    Pyro.core.initServer()
    daemon = Pyro.core.Daemon(publishhost=opts.host)
    locator = Pyro.naming.NameServerLocator()

    log.debug('Locating Pyro NS')
    ns = locator.getNS()
    daemon.useNameServer(ns)

    try:
        ns.unregister(settings.PYRO_FACADE_NAME)
    except NamingError:
        pass

    obj = RoombaFacade(daemon)

    daemon.connect(RoombaFacade(daemon), settings.PYRO_FACADE_NAME)

    # enter the server loop.
    log.info('Server started')
    daemon.requestLoop()

if __name__=="__main__":
    main()
