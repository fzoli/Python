#!/usr/bin/env python

import sys
import Skype4Py
import dbus
import dbus.glib
import gobject

class SkypeGnomePlugin:

  def __init__(self):
    self.__init_dbus()
    self.__init_skype()
    self.__start_main_loop()
    self.restoreStatus = False
  
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
  
  def __on_screen_locked(self):
    print 'Screen locked.'
    if self.skype.CurrentUserStatus == 'ONLINE':
      self.restoreStatus = True
      self.skype.ChangeUserStatus('AWAY')
  
  def __on_screen_unlocked(self):
    print 'Screen unlocked.'
    if self.restoreStatus:
      self.restoreStatus = False
      self.skype.ChangeUserStatus('ONLINE')
  
  def __on_skype_attached(self):
    print 'Skype attached.'
  
  def __on_skype_closed(self):
    print 'Skype closed.'
    self.__stop_main_loop()
  
  def __init_dbus(self):
    self.bus = dbus.SessionBus()
    self.bus.add_signal_receiver(self.__dbus_screensaver_handler, dbus_interface='org.gnome.ScreenSaver', signal_name='ActiveChanged')
  
  def __init_skype(self):
    self.skype = Skype4Py.Skype()
    if not self.skype.Client.IsRunning:
      print >>sys.stderr, 'Skype is not running.'
      sys.exit(-1)
    self.skype.FriendlyName = 'GnomePlugin'
    self.skype.OnAttachmentStatus = self.__skype_attachment_handler;
    self.skype.Attach()
  
  def __start_main_loop(self):
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    self.loop = gobject.MainLoop()
    self.loop.run()

  def __stop_main_loop(self):
    print 'Bye'
    self.loop.quit()

if __name__ == '__main__':
  SkypeGnomePlugin()
  
