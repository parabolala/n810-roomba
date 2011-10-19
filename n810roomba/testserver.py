import re
import os
import subprocess
import optparse
import logging

# import this before Pyro to override PYRO_CONFIG_FILE
from n810roomba import settings

import Pyro.naming
from Pyro.errors import NamingError

from n810roomba.pyro_facade import RoombaFacade


def detect_ip():
    if os.name != 'posix':
        res = None
    else:
        ip_pattern = re.compile(r'^(\w+):?.*?inet (?:addr:)?([0-9a-f.]+)',
                                re.M | re.S)

        ifcfg_sp = subprocess.Popen('ifconfig', stdout=subprocess.PIPE)
        ifcfg = ifcfg_sp.stdout.read()

        if_ip_list = ip_pattern.findall(ifcfg)
        # [('lo', '127.0.0.1'), ('wlan0', '192.168.1.12')]

        if len(if_ip_list) > 1:
            non_local_ifs = filter(lambda (iface, ip): not iface.startswith('lo'),
                                   if_ip_list)
            if non_local_ifs:
                res = non_local_ifs[0][1]
            else:
                res = if_ip_list[0][1]
        elif if_ip_list:
            res = if_ip_list[0][1]
        else:
            res = None
    return res

parser = optparse.OptionParser(description='Roomba n810 some bla-bla')
parser.add_option('-H', '--my-host', dest='host', action='store',
                   default=detect_ip(),
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
