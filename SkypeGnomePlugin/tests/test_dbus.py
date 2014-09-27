#!/usr/bin/env python

import sys
import exceptions
try:
  import dbus
  import dbus.glib
  import gobject
except exceptions.ImportError, e:
  print >>sys.stderr, 'Missing modules:'
  print >>sys.stderr, e
  sys.exit(4)

def on_error(exctype, value, traceback):
  global loop
  loop.quit()

def on_screen_locked():
  print 'Screen locked'

def on_screen_unlocked():
  print 'Screen unlocked'

def screensaver_handler(locked):
  if locked == 1:
    on_screen_locked()
  else:
    on_screen_unlocked()

sys.excepthook = on_error

bus = dbus.SessionBus()
bus.add_signal_receiver(screensaver_handler, dbus_interface='org.gnome.ScreenSaver', signal_name='ActiveChanged')

dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
loop = gobject.MainLoop()
loop.run()

