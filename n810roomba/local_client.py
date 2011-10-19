import time
import logging
from pprint import pprint

from n810roomba.client import LocalBot

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


def main():
    bot = LocalBot()
    pprint(bot.sensors.GetAll())
    bot.Drive(40, 200)
    time.sleep(0.7)
    bot.Drive(-40, -200)
    time.sleep(0.7)
    bot.Drive(40, 200)
    time.sleep(0.7)
    bot.Drive(-40, -200)
    time.sleep(0.7)
    bot.Drive(0, 0)

if __name__ == '__main__':
    main()

