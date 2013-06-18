#!/usr/bin/env python

import imaplib 
import time

f = open('exmailog', 'w')

info = imaplib.IMAP4_SSL('alegre.inf.utfsm.cl', 993) 
sansano = imaplib.IMAP4_SSL('imap.gmail.com')
info.login('name.lastname', 'password')
dest.login('name.lastname.xx@dest.usm.cl', 'password2')

delay_t = 5
run = True

info.select()
dest.select()

f.write('*************************\n')
f.write('looking for un-seen messages...\n')
f.write(str(time.ctime())+'\n------>delay: ' + str(delay_t) + '\n')
f.flush()

while run:
	try:
		unseen_msg_ids = info.search(None, 'UnSeen')[1][0]
		if unseen_msg_ids:
			unseen_msg_ids = unseen_msg_ids.split()
			for msg_id in unseen_msg_ids:
				f.write(str(time.ctime()) + ': new mail! id: ' + msg_id + '\n')
				f.flush()
				data = info.fetch(msg_id, '(RFC822)')[1][0][1]
				dest.append('INBOX', None, None, data)
		time.sleep(delay_t)
	except Exception:
		f.write(str(time.ctime()) + ': ERROR!\n')
		f.flush()
		run = False

f.close()
dest.close()
dest.logout()
infp.close()
info.logout()
