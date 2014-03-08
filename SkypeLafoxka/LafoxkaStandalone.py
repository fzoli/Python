#! /usr/bin/python
# coding: utf-8

import sys
import Skype4Py

import re
import requests

class Lafoxka(object):

    pageEncoding = 'ISO-8859-2'
    pt = re.compile('(<td.*?>)(.*?)(</td><td.*?>)(.*?)</td>')
    ptbl = re.compile('<td>(.*?)</td><td>(.*?)</td>')

    def __init__(self, bejeaz = '110842', embazon = '60009'):
        self.bejeaz = bejeaz
        self.embazon = embazon

    def loadSource(self, msg):
        r = requests.post('http://www.lafoxka.hu/beszelget.php?bejeaz='+self.bejeaz+'&embazon='+self.embazon, data={'valasz': msg.encode(self.pageEncoding)})
        r.encoding = self.pageEncoding
        return r.text

    def loadMessages(self, msg):
        src = self.loadSource(msg)
        #print([msg for i,name,k,msg in self.pt.findall(src) if name == 'Lafoxka'])
        msgs = []
        for i,name,k,msg in self.pt.findall(src):
            if name != 'Lafoxka': break
            if msg.startswith('<table'):
                sindex = src.index(msg)
                tbl = src[sindex:src.index('</table>',sindex)+8]
                msg = 'tbl\n'
                for code,text in self.ptbl.findall(tbl):
                    msg += code+'\t'+text+'\n'
            msg = msg.replace('<br>', '\n')
            msg = msg.replace('<p>', '\n')
            msg = msg.replace('</p>', '\n')
            msgs.append(msg)
        msgs.reverse()
        return msgs

#HOST = "localhost"
#PORT = 4444

lafoxka = Lafoxka()

# Creating instance of Skype object
skype = Skype4Py.Skype()

# Filter skype id
skypeHandle = ''
counter = 0
for x in sys.argv:
     counter = counter + 1
     if counter > 1:
          skypeHandle = x

#------------------------------------------------------------------------------------------
# Fired on attachment status change. Here used to re-attach this script to Skype in case attachment is lost.
closed = 0

def OnAttach(status): 
	print 'API attachment status: ' + skype.Convert.AttachmentStatusToText(status)
	if status == Skype4Py.apiAttachAvailable:
		skype.Attach()

	if status == Skype4Py.apiAttachSuccess:
	   print('******************************************************************************'
); 
	else:
	   global closed
	   closed = 1
	   print('Skype closed.')
		
#------------------------------------------------------------------------------------------
# Fired on chat message status change. 
# Statuses can be: 'UNKNOWN' 'SENDING' 'SENT' 'RECEIVED' 'READ'		

def OnMessageStatus(Message, Status):
	global skypeHandle
	global skype
	if Status == 'RECEIVED' and (skypeHandle == '' or Message.FromHandle == skypeHandle) and (not Message.FromHandle == skype.CurrentUser.Handle):
		print(Message.FromDisplayName + ': ' + Message.Body)
		answers = lafoxka.loadMessages(Message.Body)
		for answer in answers:
			try:
				skype.SendMessage(Message.FromHandle, answer)
				print('Lafoxka: ' + answer)
			except:
				print >>sys.stderr, "Skype message error."

#------------------------------------------------------------------------------------------
# assigning handler functions and set application name.

skype.OnAttachmentStatus = OnAttach;
skype.OnMessageStatus = OnMessageStatus;
skype.FriendlyName = 'Lafoxka'

# If Skype is not running, exit.
if not skype.Client.IsRunning:
    print >>sys.stderr, "Skype is not running."
    sys.exit(-1)

print('******************************************************************************'
);
print 'Connecting to Skype..'
skype.Attach();

#------------------------------------------------------------------------------------------
# Looping until user types 'exit' or skype closed
try:
    Cmd = ''
    while not (Cmd == 'exit' or closed == 1):
        Cmd = raw_input('');
except:
    print ''
