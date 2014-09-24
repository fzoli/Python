#!/usr/bin/env python

import sys
import Skype4Py
import dbus
import dbus.glib
import gobject
from threading import Thread
from time import sleep

class SkypeGnomePlugin:

  def __init__(self):
    self.refused = False
#    self.restoreStatus = False
    self.__init_global_error_handler()
    self.__init_dbus()
    self.__init_skype()
    self.__start_main_loop()
  
  def __dbus_screensaver_handler(self, p):
    if p == 1:
      self.__on_screen_locked()
    else:
      self.__on_screen_unlocked()
  
  def __skype_attachment_handler(self, status):
    if status == Skype4Py.apiAttachSuccess:
      self.__on_skype_attached()
    else:
      if status != Skype4Py.apiAttachRefused:
        self.__on_skype_closed()
  
  def __set_skype_status(self, status):
    Thread(target = self.skype.ChangeUserStatus, args = (status, )).start()
    print 'Set to ' + status + '.'

  def __on_screen_locked(self):
    print 'Screen has locked.'
    if self.skype.CurrentUserStatus == 'ONLINE':
#      self.restoreStatus = True
      self.__set_skype_status('AWAY')
  
  def __on_screen_unlocked(self):
    print 'Screen has been unlocked.'
#    if self.restoreStatus:
#      self.restoreStatus = False
    if self.skype.CurrentUserStatus == 'AWAY':
      self.__set_skype_status('ONLINE')
  
  def __on_skype_attached(self):
    print 'Skype plugin has attached.'
  
  def __on_skype_closed(self):
    print 'Skype has been closed.'
    self.__stop_main_loop()
  
  def __init_global_error_handler(self):
    sys.excepthook = self.__on_error

  def __init_dbus(self):
    self.bus = dbus.SessionBus()
    self.bus.add_signal_receiver(self.__dbus_screensaver_handler, dbus_interface='org.gnome.ScreenSaver', signal_name='ActiveChanged')
  
  def __init_skype(self):
    self.skype = Skype4Py.Skype()
    if not self.skype.Client.IsRunning:
      print >>sys.stderr, 'Skype is not running.'
      sys.exit(1)
    self.skype.FriendlyName = 'GnomePlugin'
    self.skype.OnAttachmentStatus = self.__skype_attachment_handler;
    self.__try_skype_attach()
    
  def __try_skype_attach(self):
    try:
      self.skype.Attach()
    except Skype4Py.errors.SkypeAPIError:
      if self.refused:
        print >>sys.stderr, 'Skype plugin access denyed.'
        sys.exit(1)
      else:
        self.refused = True
        sleep(3)
        self.__try_skype_attach()

  def __on_error(self, exctype, value, traceback):
    print 'Unexpected error.'
    self.__stop_main_loop()
    sys.__excepthook__(exctype, value, traceback)
    sys.exit(1)

  def __start_main_loop(self):
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    self.loop = gobject.MainLoop()
    self.loop.run()

  def __stop_main_loop(self):
    print 'Bye'
    if hasattr(self, 'loop'):
      self.loop.quit()
  
if __name__ == '__main__':
  SkypeGnomePlugin()
