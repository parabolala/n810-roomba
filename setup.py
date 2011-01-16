#!/usr/bin/env python

from distutils.core import setup

setup(name='n810roomba',
      version='0.1.0',
      description='A set of tools for communicating iRobot roombas via Nokia N810',
      url='https://github.com/xa4a/n810-roomba',
      author='Yevgen Varavva',
      author_email='varavv@gala.net',
      packages=['n810roomba', 'n810roomba.ui'],
      package_data={'n810roomba.ui': ['mainwindow.ui']},
      data_files=[('kernel', ['kernel/ftdi_sio.ko', 'kernel/usbserial.ko'])],
      requires=['Pyro','pyserial'],
      )
