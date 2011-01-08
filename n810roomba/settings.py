import os
import os.path as op
import logging.config


ROOT = os.path.dirname(__file__)

logging.config.fileConfig(op.join(ROOT, 'conf', "logging.conf"))
os.environ['PYRO_CONFIG_FILE'] = op.join(ROOT, 'conf', 'Pyro.conf')

PYRO_FACADE_NAME = 'roomba-facade'
PYRO_SCI_NAME = 'roomba_sci'
