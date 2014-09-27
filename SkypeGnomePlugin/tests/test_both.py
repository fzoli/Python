#!/usr/bin/env python

# Test environment:
# - Skype4Py API from https://github.com/awahlig/skype4py.git (commit 8d59590dd5f9eeb38b0fd35d218b0f14ee1ab8bb on Aug 13, 2014)
# - Skype version 4.3.0.37
# - Ubuntu 14.04 LTE (amd64 kernel 3.13.0-35-generic)

logging = True

import sys
import exceptions
try:
  import Skype4Py
  import dbus
  import dbus.glib
  import gobject
  from time import sleep
  from threading import Thread
  from threading import RLock
except exceptions.ImportError, e:
  print >>sys.stderr, 'Missing modules:'
  print >>sys.stderr, e
  sys.exit(4)

lock = RLock()
skype = Skype4Py.Skype()
skype.FriendlyName = 'GnomePluginTest'

statusMatch = False
forceAttach = False

def safe_switch_skype_status(statFrom, statTo):
  global lock, skype, statusMatch, forceAttach
  lock.acquire()
  try:
    if skype.Client.IsRunning:
      if forceAttach:
        log('Try attach.')
        skype.Attach()
      # Note: CurrentUserStatus and ChangeUserStatus call synchron attach if need; may throw exception
      if skype.CurrentUserStatus == statFrom:
        skype.ChangeUserStatus(statTo)
        statusMatch = True
        forceAttach = False
        log('Set status from ' + statFrom + ' to ' + statTo + '.')
      else:
        statusMatch = False
        log('Do not touch status; status is not ' + statFrom + '.')
    else:
      log('Status change error: Skype is not running')
  except Skype4Py.errors.SkypeAPIError, e:
    # Reasons:
    # - refuse
    # - first timeout (sets error state 68)
    statusMatch = False
    forceAttach = True
    log('Status change error: ' + str(e))
  except Skype4Py.errors.SkypeError, e:
    # Reasons:
    # - repeated timeout [may happen]
    #   stucked in error state 68, so every time exception will be thrown; only Attach() helps but it asks permission every time
    # - unknown status [source code error]
    statusMatch = False
    log('Status change error: ' + str(e))
  except exceptions.Exception, e:
    # Skype API bug (like 'NoneType' object has no attribute 'Invoke')
    # - multiple reject [may happen]
    #   do not change the error state, no problem
    statusMatch = False
    log('Status change error: ' + str(e))
  finally:
    lock.release()

def switch_skype_status(statFrom, statTo):
  Thread(target = safe_switch_skype_status, args = (statFrom, statTo)).start()

def on_error(exctype, value, traceback):
  global loop
  loop.quit()

def on_screen_locked():
  log('Screen locked.')
  switch_skype_status('ONLINE', 'AWAY')

def on_screen_unlocked():
  global lock, statusMatch
  print 'Screen unlocked.'
  lock.acquire()
  try:
    if statusMatch:
      switch_skype_status('AWAY', 'ONLINE')
    else:
      log('Status not changed.')
  finally:
    lock.release()

def screensaver_handler(locked):
  if locked == 1:
    on_screen_locked()
  else:
    on_screen_unlocked()

def log(text):
  global logging
  if logging:
    print text

sys.excepthook = on_error

bus = dbus.SessionBus()
bus.add_signal_receiver(screensaver_handler, dbus_interface='org.gnome.ScreenSaver', signal_name='ActiveChanged')

dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
loop = gobject.MainLoop()
loop.run()
