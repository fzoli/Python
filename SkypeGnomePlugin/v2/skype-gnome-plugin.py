#!/usr/bin/env python

import sys
import exceptions
try:
  import Skype4Py
  import dbus
  import dbus.glib
  import gobject
  import traceback
  from time import sleep
  from threading import Thread
  from threading import RLock
except exceptions.ImportError, e:
  print >>sys.stderr, 'Missing modules:'
  print >>sys.stderr, e
  sys.exit(1)

class SkypeGnomePlugin:

  def __init__(self, pluginName):
    self.logging = True
    self.__statusMatch = False
    self.__forceAttach = False
    self.__lock = RLock()
    self.__init_error_handler()
    self.__init_dbus()
    self.__init_skype(pluginName)

  def start(self):
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    self.loop = gobject.MainLoop()
    self.loop.run()

  def stop(self):
    if hasattr(self, 'loop'):
      self.__log('Stop.')
      self.loop.quit()

  def switch_skype_status(self, statFrom, statTo):
    thread = Thread(target = self.__switch_skype_status, args = (statFrom, statTo))
    thread.start()
    return thread

  def __init_error_handler(self):
    sys.excepthook = self.__on_error

  def __init_dbus(self):
    self.__bus = dbus.SessionBus()
    self.__bus.add_signal_receiver(self.__screensaver_handler, dbus_interface='org.gnome.ScreenSaver', signal_name='ActiveChanged')

  def __init_skype(self, pluginName):
    self.__skype = Skype4Py.Skype()
    self.__skype.FriendlyName = pluginName

  def __switch_skype_status(self, statFrom, statTo):
    self.__lock.acquire()
    try:
      if self.__skype.Client.IsRunning:
        if self.__forceAttach:
          self.__log('Try attach.')
          self.__skype.Attach()
          self.__forceAttach = False
        if self.__skype.CurrentUserStatus == statFrom:
          self.__skype.ChangeUserStatus(statTo)
          self.__statusMatch = True
          self.__log('Set status from ' + statFrom + ' to ' + statTo + '.')
        else:
          self.__statusMatch = False
          self.__log('Do not change status; status is not ' + statFrom + '.')
      else:
        self.__log('Status change error: Skype is not running')
    except Skype4Py.errors.SkypeAPIError, e:
      self.__statusMatch = False
      self.__forceAttach = True
      self.__log('Status change API error: ' + str(e))
    except Skype4Py.errors.SkypeError, e:
      self.__statusMatch = False
      self.__log('Status change general error: ' + str(e))
    except exceptions.Exception, e:
      self.__statusMatch = False
      self.__log('Status change unexpected error: ' + str(e))
    finally:
      self.__lock.release()

  def __on_error(self, exctype, value, tb):
    self.stop()
    if exctype != exceptions.KeyboardInterrupt:
      print >>sys.stderr, 'Unexpected error'
      traceback.print_exception(exctype, value, tb)

  def __on_screen_locked(self):
    self.__log('Screen has locked.')
    self.switch_skype_status('ONLINE', 'AWAY')

  def __on_screen_unlocked(self):
    self.__log('Screen has unlocked.')
    self.__lock.acquire()
    try:
      if self.__statusMatch:
        self.switch_skype_status('AWAY', 'ONLINE')
      else:
        self.__log('Status was not changed.')
    finally:
      self.__lock.release()

  def __screensaver_handler(self, locked):
    if locked == 1:
      self.__on_screen_locked()
    else:
      self.__on_screen_unlocked()

  def __log(self, text):
    if self.logging:
      print text

if __name__ == '__main__':
  SkypeGnomePlugin('SkypeGnomePlugin').start()
