#!/usr/bin/env python

import imaplib 
import time

class LogType:
	pass

LOGFILENAME = 'exmailog'
OUTPUT = 'logfile'

if OUTPUT == 'screen':
	import sys
	outstream = sys.stdout
else:
	outstream = open(LOGFILENAME, 'w')

_TYPE = LogType()
_TYPE.newmail = 'new mail!'
_TYPE.warning = 'warning'
_TYPE.error = 'ERROR'
_TYPE.critical = 'CRITICAL!!!'
_TYPE.info = 'info'

def formatlog(type, msg):
	return str(time.ctime()) + ': ' + str(type) + ': ' + str(msg) + '\n'

class IMAP_CONN (imaplib.IMAP4_SSL):
	def __init__(self, args):
		self.__un_seen = None
		self.__hostimap = args['host']
		self.__portimap = args['port']
		self.__username = args['user']
		self.__password = args['pass']
		self.__boxmail = args['boxmail']
		if self.__portimap:
			outstream.write(formatlog(_TYPE.info, 'connecting with server using port: %d' % self.__portimap))
			outstream.flush()
			imaplib.IMAP4_SSL.__init__(self, self.__hostimap, self.__portimap)
		else:
			outstream.write(formatlog(_TYPE.info, 'connecting with server with default port'))
			outstream.flush()
			imaplib.IMAP4_SSL.__init__(self, self.__hostimap)
		self.login(self.__username, self.__password)
		self.select(self.__boxmail)

	def update_conn(self, boxmail=None):
		try:
			self.login(self.__username, self.__password)
		except Exception:
			outstream.write(formatlog(_TYPE.warning, 'couldnt be logged into the account...'))
		if boxmail:
			self.select(boxmail)
			self.__boxmail = boxmail
		else:
			self.select(self.__boxmail)
	
	def check_unread(self):
		status, body = self.search(None, 'UnSeen')
		if status and body[0]:
			self.__un_seen = body[0]
			return True
		self.__un_seen = None
		return None
		
	def walk_unread(self):
		if self.__un_seen:
			for m in self.__un_seen.split():
				outstream.write(formatlog(_TYPE.newmail, m))
                                outstream.flush()
				status, body = self.fetch(m, '(RFC822)')
				if status == 'OK' and body[0][1]:
					yield body[0][1]
				else:
					break

	def addmail(self, data):
		self.append(self.__boxmail, None, None, data)

info1 = {
	'host': 'alegre.inf.utfsm.cl',
	'port': 993,
	'user': 'name.lastname',
	'pass': 'password123',
	'boxmail': 'INBOX'
}

info2 = {
	'host': 'imap.gmail.com',
	'port': None,
	'user': 'name.lastname.xx@sansano.usm.cl',
	'pass': 'password123',
	'boxmail': 'INBOX'
}

class ImaP:
	pass

imap = ImaP()
imap.origin = IMAP_CONN(info1)
imap.dest = IMAP_CONN(info2)

limit_error = 10
delay_t = 7
run = True
num_errors = 0

def putheader(fp):
	fp.write('*************************\n')
	fp.write('looking for un-seen mails...\n')
	fp.write(formatlog('------> delay', str(delay_t)))
	fp.flush()

putheader(outstream)

while run:
	try:	
		if (imap.origin.check_unread()):
			outstream.write(formatlog(_TYPE.info, 'something is in mailbox... looking for gold'))
			outstream.flush()
			for data in imap.origin.walk_unread():
				#print data
				imap.dest.addmail(data)
				outstream.write(formatlog(_TYPE.info, 'synchronized sucessfully!'))
				outstream.flush()
		time.sleep(delay_t)
	except Exception:
		try:
			outstream.write(formatlog(_TYPE.error, 'something was happening'))
			outstream.flush()
			outstream.write(formatlog(_TYPE.info, 'Trying reconnection...'))
			outstream.flush()
			imap.origin.update_conn()
			imap.dest.update_conn()
		except Exception:
			num_errors += 1
			outstream.write(formatlog(_TYPE.error, 'failed attempt to reconnect!'))
			outstream.flush()
		if (num_errors >= limit_error):
			outstream.write(formatlog(_TYPE.error, 'number of aceptable errors was reached, quitting!'))
			outstream.flush()
			run = False
		time.sleep(10)

outstream.write(formatlog(_TYPE.info, 'closing mailboxes...'))
outstream.flush()
imap.origin.close()
imap.dest.close()
outstream.write(formatlog(_TYPE.info, 'logging out connections...'))
outstream.flush()
imap.origin.logout()
imap.dest.logout()
outstream.write('BYEBYE!\n')
outstream.flush()

if OUTPUT != 'screen':
	outstream.close()
