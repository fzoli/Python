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
  from time import sleep
  from threading import Thread
  from threading import Lock
except exceptions.ImportError, e:
  print >>sys.stderr, 'Missing modules:'
  print >>sys.stderr, e
  sys.exit(4)

lock = Lock()
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
        forceAttach = False
      # Note: CurrentUserStatus and ChangeUserStatus call synchron attach if need; may throw exception
      if skype.CurrentUserStatus == statFrom:
        skype.ChangeUserStatus(statTo)
        statusMatch = True
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

def log(text):
  global logging
  if logging:
    print text

tryReAttach = True

def try_attach():
  global skype, tryReAttach
  if skype.Client.IsRunning:
    try:
      log('Try attach.')
      skype.Attach()
    except:
      log('Attach failed.')
      if tryReAttach:
        tryReAttach = False
        sleep(3)
        try_attach()
  else:
    log('Skype is not running.')

try_attach()

switch_skype_status('INVISIBLE', 'INVISIBLE')
sleep(30)
switch_skype_status('INVISIBLE', 'ONLINE')
sleep(5)
switch_skype_status('ONLINE', 'INVISIBLE')

