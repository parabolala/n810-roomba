import os
import os.path as op


ROOT = os.path.dirname(__file__)

try:
    import logging.config
    logging.config.fileConfig(op.join(ROOT, 'conf', "logging.conf"))
except ImportError:
    pass
os.environ['PYRO_CONFIG_FILE'] = op.join(ROOT, 'conf', 'Pyro.conf')

PYRO_FACADE_NAME = 'roomba-facade'
PYRO_SCI_NAME = 'roomba_sci'
