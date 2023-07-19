# InterMapper script to test round trip time for an email message
# Author: Josh Levinger
# Changes - June 2007 -spr
# Updated for IMDC Python interpreter
# Ported reb's error checking from POP probe
# 27Dec2007 - minor tweaks to align with pop probe -reb
# 04Dec2009 - included as companion script in probe. -cls
# 12Mar2011 - Modified to add '\Deleted' to messages and use expunge() to remove them. -reb

''' Sample command (on one line)
/usr/local/imdc/core/python/bin/imdc -OO imap_roundtrip.py --to=intermapper1@pstat.ucsb.edu --user=intermapper1 --pass=WqeC94Di --imapserver=mail.pstat.ucsb.edu --from=intermapper2@pstat.ucsb.edu --smtpuser=intermapper2 --smtppass=nbK717V1 --smtpserver=mail.pstat.ucsb.edu --timeout=30
'''
import imaplib, smtplib
import email.Message
import time
import sys, getopt
import socket

class ImapProbe:

	def __init__(self):
		#IMAP Variables
		self.imap_host = None
		self.imap_user = None
		self.imap_pwrd = None

		#SMTP Variables
		self.smtp_server = None #default to imap_host in main()
		self.to_addr = None #default to imap_user@imap_host in main()
		self.from_addr = None #default to intermapper@example.com in main()
		self.smtp_user = None #auth SMTP
		self.smtp_pass = None #auth SMTP
		
		#Internal Variables
		self.mbox = None
		self.mbox_size = 0		#number of messages in the mailbox
		self.msg = email.Message.Message() #the message, used for continuity check
		self.msg_length = 100	#length of sent message, should be ~89
		self.time_sent = 0	 	#time probe message was sent
		self.time_start = 0		#time the program started
		self.timeout = 60		#default timeout of 60 seconds
		self.msg_found = False	#have we found the message yet?
		self.roundtrip = 0		#the data that we will report
		self.hops = 0			#the data that we will report
		self.num_old_probes = 0	#number of old probes found, if > 0, warn


	##########
	###Connect to IMAP mailbox
	#########
	def connect_imap(self,host=None, user=None, pwrd=None):
		"""Login to the IMAP4 server"""
		try:
			self.mbox = imaplib.IMAP4(host)
			if self.mbox.login(user,pwrd)[0] == 'OK':
				self.mbox_size = int(self.mbox.select('INBOX')[1][0])
				return True
		except imaplib.IMAP4.error, e:	
			self.error("[IMAP] Cannot login: " + str(e),1)
		except socket.gaierror, e:
			self.error("[IMAP] Address error: " + str(e),2)
		except:
			self.error("[IMAP] Couldn't connect to host '" + host + "'", 3)
		return False

	######### 
	###Connect to SMTP server, and place message in box
	#########
	def send_message(self, smtpserver=None,toaddr=None,fromaddr=None,smtpuser=None,smtppass=None):
		"""Connect to server, create email message, place current time in X-TimeSent header, and return boolean status."""
		
		payload = "Email round trip probe message from InterMapper. This message will self destruct in %i seconds." % self.timeout
		payload = payload + "\nTime Sent: %s" % time.asctime(time.localtime())
		try: #connect to smtp server
			server = smtplib.SMTP(smtpserver) 
		except socket.gaierror, e:
			self.error("[SMTP] Address error: " + str(e), 2)
		except :
			self.error("[SMTP] Address error", 2)
		#server.set_debuglevel(1)
		if smtpuser != None or smtppass != None:
			try: 	#use authenticated smtp
				server.login(smtpuser, smtppass)	
			except smtplib.SMTPException, e:
				self.error("[SMTP] Authentication Error: " + str(e),1)
			except :
				self.error("[SMTP] Login error", 1)
		self.msg["To"]=toaddr
		self.msg["From"]=fromaddr
		self.msg["Subject"]="InterMapper_Probe"
		self.msg["X-Mailer"]="InterMapper"
		self.msg.set_payload(payload, "quoted-printable")
		self.time_sent = time.time() #START CLOCK
		self.msg["X-TimeSent"]=str(self.time_sent)
#		print "Sending message at %s" % self.time_sent
		try:
			server.sendmail(self.msg.get("From"), self.msg.get("To"), self.msg.as_string()) #send message
			sent_ok = True
		except smtplib.SMTPException, e:
			self.error("[SMTP] Sendmail error: " + str(e),1)
			sent_ok = False
		except :
			self.error("[SMTP] Error sending e-mail", 1)
		server.quit()
		return sent_ok

	##########
	###Search through IMAP mailbox for message with correct subject
	##########
	def check_for_message(self):
		typ, data = self.mbox.select('INBOX')
#		print typ, data
		num_msgs = int(data[0])
#		print "There are %d messages in INBOX" % num_msgs
		
		if num_msgs == 0: # no probe messages have arrived yet
			self.msg_found = False
#			print "None found yet"
		else:
			typ, found_messages = self.mbox.search(None, '(SUBJECT "InterMapper_Probe")') 
#			print "Found %d candidates" % len(found_messages)
#			print "Found Messages: ", found_messages
			for n in found_messages[0].split():
#				print n
				msg_string = self.mbox.fetch(n,'(RFC822)')[1][0][1] #get the message
				self.mbox.store(n, 'FLAGS', '\Seen') #mark message as seen
				rcvd_msg = email.message_from_string(msg_string) #convert to email format
				msg_sender = rcvd_msg.get('From')
				msg_xmailer = rcvd_msg.get('X-Mailer')
				msg_xtimesent = rcvd_msg.get('X-TimeSent')
				if msg_xmailer == "InterMapper" and msg_sender == self.from_addr: #it's a probe message
					if msg_xtimesent == str(self.time_sent): #this is the probe message we just sent
						self.roundtrip = self.time_elapsed() #STOP CLOCK
						rcvd_headers = rcvd_msg.get_all("Received")
						self.hops = len(rcvd_headers) #count number of hops
						#if self.msg.get_payload() != rcvd_msg.get_payload():
						#	self.error("Message changed in transit", 1) #not sure why this would be called, but here it is
#						print "Found it in msg %s! Time is: %s " % (n, msg_xtimesent)
						self.msg_found = True
					else: #it's an old probe message
 						self.num_old_probes += 1
#						print "Not in msg %s: time was %s" % (n, msg_xtimesent)
					typ, response = self.mbox.store(n, '+FLAGS', r'(\Deleted)') # delete it in any event
#			--- at end of loop...
			typ, response = self.mbox.expunge()			# and expunge all the deleted messages
		return None

	def error(self, e=None, exit_code=None):
		"""Send an error message to stdout, and use exit code to send state to InterMapper
		codes are interpreted as follows: (0=ok, 1=warn, 2=alarm, 3=down)"""
		
#		print "{ $rtt := 0, $hop := 0 } "; #must be first thing printed for IM to report correctly
		print e
		if self.num_old_probes > 0:
			exit_code = 1
			print self.num_old_probes, "old messages found"
		raise SystemExit, exit_code #pass exit code to Intermapper for state change

	def time_elapsed(self):
		elapsed = time.time() - self.time_sent
		if elapsed > self.timeout:
			self.error("Time Limit Exceeded. Message not received within %d seconds." % (self.timeout), 2) #message not received w/in timeout, alarm
		return elapsed

	def usage(self):
		print "usage: --host=<hostname> --user=<username> --pass=<password> --smtpserver=<smtp server hostname> --smtpuser=<smtp username> --smtppass=<smtp password> --to=<email address> --from=<email address> --timeout=<seconds>"
		raise SystemExit

	##########
	###Send message, and wait for it to appear, with timeouts and whatnot
	##########
	def main(self):
		#variable checks
		if self.imap_host is None:
			self.usage()
		if self.to_addr is None:
			self.error("'Email to' field empty",1)
		if self.smtp_server is None: #default to imap_host
			self.smtp_server = str(self.imap_host)
		if self.from_addr is None: #default to intermapper@example.com
			self.from_addr = "intermapper@example.com"
			
		if self.connect_imap(self.imap_host,self.imap_user,self.imap_pwrd): #connect to imap
			if self.send_message(self.smtp_server,self.to_addr,self.from_addr,self.smtp_user,self.smtp_pass): #connect to smtp
				while self.time_elapsed() < self.timeout and not self.msg_found: #stay in the mailbox until the message arrives
					try:
						self.check_for_message()
						if not self.msg_found: #wait 1 sec and try again
#							print "not found yet"
							time.sleep(1)
					except imaplib.IMAP4.error, e:
						self.error("[IMAP] Message check error: " + str(e),1)
				try:
					self.mbox.close() #to commit changes
					self.mbox.logout() #exit IMAP gracefully
				except imaplib.IMAP4.error, e:
					self.error("[IMAP] Mailbox Close Error: " + str(e),1)
				except :
					self.error("[IMAP] Error ", 2)
			else:
				#all errors should be caught in subroutines
				self.error("[SMTP] Unforseen error. Could not send message.", 2)
		else:
			self.error("[IMAP] Unforseen error. Could not connect to IMAP server.", 2)
		return None


if __name__ == "__main__":
	def check(arg):
		"""Return the argument as a string if it exists. If not, return None. Used to type cast input from InterMapper."""
		if arg == '' or arg is None: #InterMapper puts spaces in for blank values
			return None
		else:
			return str(arg) #explicitly type-cast

	p = ImapProbe()
	try:
		opts, args = getopt.getopt(sys.argv[1:], "h:u:p:s:a:l:t:f:x:", ["imapserver=", "user=", "pass=", "smtpserver=", "smtpuser=", "smtppass=", "to=", "from=", "timeout="])
	except getopt.GetoptError, e:
		p.usage()
	for o,a in opts:
		if o in ("-h", "--imapserver"):
			p.imap_host = check(a)
		elif o in ("-u", "--user"):
			p.imap_user = check(a)
		elif o in ("-p", "--pass"):
			p.imap_pwrd = check(a)
		elif o in ("-s", "--smtpserver"):
			p.smtp_server = check(a)
		elif o in ("-a", "--smtpuser"):
			p.smtp_user = check(a)
		elif o in ("-l", "--smtppass"):
			p.smtp_pass = check(a)
		elif o in ("-t", "--to"):
			p.to_addr = check(a)
		elif o in ("-f", "--from"):
			p.from_addr = check(a)
		elif o in ("-x", "--timeout"):
			p.timeout = float(a)
	p.time_start = time.time() #start clock for mailbox timeout
	p.main()
	print "\{ $rtt := %d, $hop := %d } Round trip is about %d seconds." % (p.roundtrip, p.hops, p.roundtrip)
	sys.exit(0)