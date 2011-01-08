import time

import Pyro.naming, Pyro.core
from Pyro.errors import NamingError

import settings

locator = Pyro.naming.NameServerLocator()
ns = locator.getNS()
try:
        URI=ns.resolve(settings.PYRO_FACADE_NAME)
        print 'URI:',URI
except NamingError,x:
        print 'Couldn\'t find object, nameserver says:',x
        raise SystemExit

# create a proxy for the Pyro object, and return that
test = Pyro.core.getProxyForURI(URI)

bot = test.make_roomba('bot1', '/dev/ttyUSB0', baud=115200)

bot.Control()
bot.Drive(20, 50)
time.sleep(0.5)
bot.Drive(-20, 50)
time.sleep(0.5)
bot.Drive(0, 0)
