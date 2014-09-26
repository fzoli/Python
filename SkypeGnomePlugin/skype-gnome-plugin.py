#!/usr/bin/env python

import sys
try:
  import exceptions
  import Skype4Py
  import dbus
  import dbus.glib
  import gobject
  from threading import Thread
  from time import sleep
except:
  print >>sys.stderr, 'Missing modules.'
  sys.exit(4)

class SkypeGnomePlugin:

  def __init__(self):
    self.statusMatch = False
    self.skypeAttached = False
    self.refused = False
    
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
      else:
        pass # NOTE: executes only the first time
  
  def __is_skype_status(self, status):
    if self.skypeAttached:
      return self.skype.CurrentUserStatus == status
    else:
      return False
  
  def __switch_skype_status(self, statFrom, statTo):
    if self.skypeAttached:
      if self.__is_skype_status(statFrom):
        self.statusMatch = True
        self.skype.ChangeUserStatus(statTo)
        print 'Set status from ' + statFrom + ' to ' + statTo + '.'
      else:
        self.statusMatch = False
        print 'Do not touch status; status is not ' + statFrom + '.'
  
  def switch_skype_status(self, statFrom, statTo):
    Thread(target = self.__switch_skype_status, args = (statFrom, statTo)).start()
  
  def __on_screen_locked(self):
    print 'Screen has locked.'
    self.switch_skype_status('ONLINE', 'AWAY')
      
  def __on_screen_unlocked(self):
    print 'Screen has been unlocked.'
    if self.statusMatch:
      self.switch_skype_status('AWAY', 'ONLINE')
    else:
      print 'Do not touch status; status was not changed on screen lock.'
    
  def __on_skype_attached(self):
    print 'Skype plugin has attached.'
    self.skypeAttached = True
  
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
      # TODO: attach doesn't throw exception on the second API reject, app will close only when skype will be closed
    except Skype4Py.errors.SkypeAPIError:
      if self.refused:
        print >>sys.stderr, 'Skype plugin access denyed.'
        sys.exit(2)
      else:
        self.refused = True
        sleep(3)
        self.__try_skype_attach()

  def __on_error(self, exctype, value, traceback):
    self.__stop_main_loop()
    if exctype != exceptions.KeyboardInterrupt:
      print >>sys.stderr, 'Unexpected error.'
      sys.__excepthook__(exctype, value, traceback)
      sys.exit(3)

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
