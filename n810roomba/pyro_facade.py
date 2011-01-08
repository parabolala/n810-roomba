import Pyro.core
import pyrobot


class Roomba(Pyro.core.ObjBase, pyrobot.Roomba):
    pass


