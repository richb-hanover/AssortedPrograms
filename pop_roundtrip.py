# InterMapper Proscriptbe to test round trip time for an email message
# Author: Josh Levinger
# Minor changes to error handling, error messages & return codes 28Dec2007 -reb
# Added as a companion script to POP Email Round-trip probe 04Dec2009 -cls
# 11Mar2011 - Reworking to match logic in imap version

import poplib, smtplib
import email.Message
import time
import sys, getopt
import socket

class PopProbe:

	def __init__(self):
		#POP Variables
		self.pop_host = None
		self.pop_user = None
		self.pop_pwrd = None

		#SMTP Variables
		self.smtp_server = None #default to pop_host in main()
		self.to_addr = None #default to pop_user@pop_host in main()
		self.from_addr = None #default to intermapper@example.com in main()
		self.smtp_user = None #auth SMTP
		self.smtp_pass = None #auth SMTP
		
		#Internal Variables
		self.mbox = None
		self.mbox_dict = {}		#a dictionary representation of the mbox
		self.msg = email.Message.Message() #the message, used for continuity check
		self.msg_length = 200	#length of sent message, should be 118, but still calculated
		self.time_sent = 0	 	#time probe was sent
		self.time_start = 0		#time the program started
		self.timeout = 60		#default timeout of 60 seconds
		self.msg_found = False	#have we found the message yet?
		self.roundtrip = 0		#the data that we will report
		self.hops = 0			#the data that we will report
		self.num_old_probes = 0	#number of old probes found, if > 0, warn


	##########
	###Connect to POP mailbox
	#########
	def connect_pop(self,host=None, user=None, pwrd=None):
		"""Login to the POP3 server using APOP, if available. Otherwise try USER and PASS."""
		try:
			self.mbox = poplib.POP3(host)		#Connect to the specified server
			self.mbox.apop(user,pwrd)			#Try APOP
			return True							#APOP Successful
		except poplib.error_proto, e:
			if str(e).find('APOP') >= 0:		#APOP not supported?
				try:
					resp = self.mbox.user(user)	#Send 'USER' command
					if resp.count('PASS') > 0:
						self.mbox.pass_( pwrd)	#Send 'PASS' command, if requested
					return True
				except poplib.error_proto, e:
					if str(e).find('Mailbox is already in use.') >= 0:
						pass #mailbox in use, try again in main()
					else:
						self.error("[POP3] Authentication Error: " + str(e),1)
		except socket.gaierror, e:
			self.error("[POP3] Address error: " + str(e),2)
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
		self.msg.set_payload(payload) #, "quoted-printable")
		self.time_sent = time.time() #START CLOCK
		self.msg["X-TimeSent"]=str(self.time_sent)
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

	######
	###Gets the number of messages in the mailbox. Called each time we check, so we don't go out of bounds
	#######
	def update_mbox_length(self):
		stat = self.mbox.stat()
		self.num_msg = stat[0]
		return None

	##########
	###Search through POP mailbox looking for message
	##########
	def check_for_message(self):
		self.update_mbox_length()
		mbox_list = self.mbox.list()[1] #a list of message indices and their lengths
		for n in range(len(mbox_list)): #convert list of chars into dictionary
			(key, value) = mbox_list[int(n) - 1].split()
			self.mbox_dict[int(key)] = int(value)
		for k,v in self.mbox_dict.iteritems():
			if v <= self.msg_length: #only retrieve messages that are shorter than the known length of the probe
				#print "retrieving", k
				retrieved_msg = self.mbox.retr(k)[1]
				msg_string = '\n'.join(retrieved_msg)
				rcvd_msg = email.message_from_string(msg_string)
				msg_subject = rcvd_msg.get('Subject')
				msg_xmailer = rcvd_msg.get('X-Mailer')
				msg_xtimesent = rcvd_msg.get('X-TimeSent')
				if msg_xmailer == "InterMapper" and msg_subject == "InterMapper_Probe": #it's a probe
					#print "probe"
					if msg_xtimesent == str(self.time_sent): #this is the probe we just sent
							#print "our probe"
							self.roundtrip = self.time_elapsed() #STOP CLOCK
							rcvd_headers = rcvd_msg.get_all("Received")
							self.hops = len(rcvd_headers) #count number of hops
							#if self.msg.get_payload() != rcvd_msg.get_payload():
							#	self.error("Message changed in transit", 1) #not sure why this would be called, but here it is
							self.msg_found = True
							self.mbox.dele(k) #destroy the evidence
							self.mbox.quit() #close connection and commit changes
					else: #it's an old probe
						self.num_old_probes += 1
						self.mbox.dele(k)  #destroy the evidence
						self.update_mbox_length()
		self.mbox_dict = {} #clear dictionary, for rebuild on next check
		return None

	def error(self, e=None, exit_code=None):
		"""Send an error message to stdout, and use exit code to send state to InterMapper
		codes are interpreted as follows: (0=ok, 1=warn, 2=alarm, 3=down)"""
		
		#print "\{ $rtt := 'n/a', $hop := 'n/a' }" #must be first thing printed for IM to report correctly
		print e
		if self.num_old_probes > 0:
			exit_code = 1
			print self.num_old_probes, "old messages found"
		#print "exiting, errcode = ", exit_code
		raise SystemExit, exit_code #pass exit code to Intermapper for state change

	def time_elapsed(self):
		elapsed = time.time() - self.time_sent
		if elapsed > self.timeout:
			self.mbox.quit() #if timeout, quit to remove deleted messages
			self.error("Time Limit Exceeded. Message not received within %d seconds." % (self.timeout), 2)
		return elapsed

	def usage(self):
		print "usage: --popserver=<hostname> --user=<username> --pass=<password> --smtpserver=<smtp server hostname> --smtpuser=<smtp username> --smtppass=<smtp password> --to=<email address> --from=<email address> --timeout=<seconds>"
		raise SystemExit

	##########
	###Send message, and wait for it to appear, with timeouts and whatnot
	##########
	def main(self):
		#variable checks
		if self.pop_host is None:
			self.usage()
		if self.to_addr is None:
			self.error("'Email to' field empty",1)
		if self.smtp_server is None: #default to pop_host
			self.smtp_server = str(self.pop_host)
		if self.from_addr is None: #default to intermapper@example.com
			self.from_addr = "intermapper@example.com"
		
		while not self.connect_pop(self.pop_host,self.pop_user,self.pop_pwrd): #connect to pop
			if (time.time() - self.time_start) > self.timeout:
				self.error("[POP3] Mailbox is already in use and unavailable for %i seconds." % self.timeout,3) #mailbox in use, down
			else:
				time.sleep(5) #wait 5 seconds, and try again

		if self.send_message(self.smtp_server,self.to_addr,self.from_addr,self.smtp_user,self.smtp_pass): #connect to smtp
			#print "send"
			while self.time_elapsed() < self.timeout and not self.msg_found: #stay in the mailbox until the message arrives
				try:
					self.check_for_message()
					if not self.msg_found: #wait 10 sec and try again
						time.sleep(10)
				except poplib.error_proto, e:
					self.error("[POP3] Message check error: " + str(e), 2)
		else:
			#all errors should be caught in subroutines
			self.error("[SMTP] Unforseen error. Could not send message.", 2)
		return None		


if __name__ == "__main__":
	def check(arg):
		"""Return the argument as a string if it exists. If not, return None. Used to type cast input from InterMapper."""
		if arg == '' or arg is None: #if not assigned on command line
			return None
		else:
			return str(arg) #explicitly type-cast

	p = PopProbe()
	try:
		opts, args = getopt.getopt(sys.argv[1:], "h:u:p:s:a:l:t:f:x:", ["popserver=", "user=", "pass=", "smtpserver=", "smtpuser=", "smtppass=", "to=", "from=", "timeout="])
	except getopt.GetoptError, e:
		p.usage()
		#p.error("Bad parameters: " + str(e), 1)
	for o,a in opts:
		if o in ("-h", "--popserver"):
			p.pop_host = check(a)
		elif o in ("-u", "--user"):
			p.pop_user = check(a)
		elif o in ("-p", "--pass"):
			p.pop_pwrd = check(a)
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
	p.time_start = time.time() #start clock for pop timeout
	p.main()
	print "\{ $rtt := %d, $hop := %d }" % (p.roundtrip, p.hops) #report data to InterMapper
	sys.exit(0)