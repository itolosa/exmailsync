exMailSync
============
Synchronize your mail messages from an external mail to another mail using IMAP protocol.

Example:
If you want to sync an external email account `foobar@example.com` into a gmail account `foobar@gmail.com`, you should configure the script as follows:

    info = imaplib.IMAP4_SSL('imap.example.com', 993) # change 993 by other port if necessary
    dest = imaplib.IMAP4_SSL('imap.gmail.com')
    info.login('foobar', 'password')
    dest.login('foobar', 'password2')
    ...

> Check out `exmailog` file in the current directory.

