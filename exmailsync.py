#!/usr/bin/env python

import imaplib 
import time
import getpass
import os
import sys
from daemon import Daemon

LOGFILENAME = 'exmail.stdout.log'
OUTPUT = 'log'

if OUTPUT == 'screen':
	import sys
	outstream = sys.stdout
else:
	outstream = open(LOGFILENAME, 'w')

class LogType:
	pass

error_type = LogType()
error_type.newmail = 'New Mail'
error_type.warning = 'Warning'
error_type.error = 'ERROR'
error_type.critical = 'CRITICAL'
error_type.info = 'Info'

class ImapSSLConn(object):
	def __init__(self, args):
		# variables de configuracion
		self.un_seen = None
		self.hostimap = args['host']
		self.portimap = args['port']
		self.username = args['user']
		self.password = args['pass']
		self.boxmail = args['boxmail']
		self.conn = None


	def format_log(self, errtype, msg):
		return str(time.ctime()) + ': ' + self.hostimap + ': ' + str(errtype) + ': ' + str(msg) + '\n'

	def send_error(self, errtype, msg):
		outstream.write(self.format_log(errtype, msg))
		outstream.flush()
		raise Exception

	def send_info(self, errtype, msg):
		outstream.write(self.format_log(errtype, msg))
		outstream.flush()

	def connect(self):
		# comprueba que puerto usar
		try:
			if self.portimap:
				self.send_info(error_type.info, 'Connecting with server using port: %d' % self.portimap)
				self.conn = imaplib.IMAP4_SSL(self.hostimap, self.portimap)
			else:
				self.send_info(error_type.info, 'Connecting with server with default port')
				self.conn = imaplib.IMAP4_SSL(self.hostimap)
			
			self.conn.login(self.username, self.password)
			self.conn.select(self.boxmail)
		finally:
			self.send_info(error_type.error, 'Couldnt be logged into the account')

	def close_conn(self):
		#self.conn.close()
		try:
			self.conn.logout()
		except:
			pass

	def reconnect(self):
		self.close_conn()
		self.connect()

	def check_msg(self):
		status, body = self.conn.search(None, 'UnSeen')
		if status and body[0]:
			self.un_seen = body[0]
			return True
		self.un_seen = None
		return None
		
	def walk_msg(self):
		if self.un_seen:
			for m in self.un_seen.split():
				self.send_info(error_type.newmail, m)
				status, body = self.conn.fetch(m, '(RFC822)')
				if status == 'OK' and body[0][1]:
					yield body[0][1]
				else:
					break

	def addmail(self, data):
		self.conn.append(self.boxmail, None, None, data)


class SyncManager(object):
	def __init__(self, origconf, destconf):
		self.origin = ImapSSLConn(origconf)
		self.dest = ImapSSLConn(destconf)
		self.dest.connect()
		self.origin.connect()

	def format_log(self, errtype, msg):
		return str(time.ctime()) + ': ' + str(errtype) + ': ' + str(msg) + '\n'

	def send_error(self, errtype, msg):
		outstream.write(self.format_log(errtype, msg))
		outstream.flush()
		raise Exception

	def send_info(self, errtype, msg):
		outstream.write(self.format_log(errtype, msg))
		outstream.flush()

	def sync_forever(self):
		wait_retry = 10
		limit_error = 10
		delay_t = 1
		run = True
		num_errors = 0

		outstream.write('*************************\n')
		outstream.write('checking mailbox...\n')
		outstream.write(self.format_log('------> delay', str(delay_t)))
		outstream.flush()

		while run:
			try:
				if self.origin.check_msg():
					self.send_info(error_type.info, 'new msg, checking content...')
					for data in self.origin.walk_msg():
						#cp mail in INBOX
						while num_errors < limit_error:
							try:
								self.dest.addmail(data)
								self.dest.close_conn()
								self.send_info(error_type.info, 'synchronized sucessfully!')
							except Exception:
								self.dest.reconnect()
								num_errors += 1
								continue
							break
				#wait delay_t before check again for new messages
				time.sleep(delay_t)
			except Exception:
				try:
					self.send_info(error_type.error, 'Posibly not connected')
					self.send_info(error_type.info, 'Trying reconnection...')
					self.origin.reconnect()
					num_errors += 1
				except Exception:
					num_errors += 1
					self.send_info(error_type.error, 'Failed attempt to reconnect!')
				if (num_errors >= limit_error):
					self.send_info(error_type.error, 'Error count limit exceded')
					run = False
				#wait before retry
				#time.sleep(wait_retry)

		self.send_info(error_type.info, 'logging out connections...')
		self.origin.close_conn()
		self.dest.close_conn()
		outstream.close()

class SyncDaemon(Daemon):

	def __init__(self, pid):
		self.stdin = '/dev/null'
		self.stdout = '/dev/null'
		self.stderr = '/dev/null'
		self.pidfile = pid

	def setconf(self):
		print 'inf (origin) pass: ',
		self.origin_mailbox = {
			'host': 'alegre.inf.utfsm.cl',
			'port': 993,
			'user': 'ignacio.tolosa',
			'pass': getpass.getpass(),
			'boxmail': 'INBOX'
		}

		print 'gmail (dest) pass: ',
		self.dest_mailbox = {
			'host': 'imap.gmail.com',
			'port': None,
			'user': 'ignacio.tolosa.12@sansano.usm.cl',
			'pass': getpass.getpass(),
			'boxmail': 'INBOX'
		}

	def run(self):
		self.conn = SyncManager(self.origin_mailbox, self.dest_mailbox)
		self.conn.sync_forever()


if __name__ == "__main__":
    daemon = SyncDaemon('/tmp/sync-manager.pid')
    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            daemon.setconf()
            daemon.start()
        elif 'stop' == sys.argv[1]:
            daemon.stop()
        elif 'restart' == sys.argv[1]:
            daemon.restart()
        else:
            print "Unknown command"
            sys.exit(2)
    	sys.exit(0)
    else:
        print "usage: %s start|stop|restart" % sys.argv[0]
        sys.exit(2)