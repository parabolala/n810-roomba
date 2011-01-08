import time

import pyrobot

import Pyro.naming, Pyro.core
from Pyro.errors import NamingError

import settings

locator = Pyro.naming.NameServerLocator()
ns = locator.getNS()
try:
        URI = ns.resolve(settings.PYRO_FACADE_NAME)
        print 'URI:',URI
except NamingError,x:
        print 'Couldn\'t find object, nameserver says:',x
        raise SystemExit

# create a proxy for the Pyro object, and return that
test = Pyro.core.getProxyForURI(URI)

test.make_sci('roomba_sci', tty='/dev/cu.usbserial-FTTL3AW0', baud=115200)

#test.make_roomba(pyro_name='bot1')
#bot = test.bot
sci = Pyro.core.getProxyForURI(ns.resolve('roomba_sci'))

bot = pyrobot.Roomba(notty=True)
bot._set_sci(sci)


bot.Control()
bot.Drive(20, 50)
time.sleep(0.5)
bot.Drive(-20, 50)
time.sleep(0.5)
bot.Drive(0, 0)
