#!/usr/local/imdc/core/python/bin/imdc -OO
'''
This plugin was created to utilize Amazon Web Services CloudWatch API.
It queries any one of the CloudWatch statistics such as CPU utilization,
disk I/O, or network I/O.

The InterMapper probe files in this distribution automatically call this
plugin. They should be placed in the Probes directory of the InterMapper
Settings directory.

This program, as well as the other files named below should be placed in
the Tools directory.

Arguments:

instance-id - the instance ID of the AMI you wish to monitor
Metric Name - CloudWatch API currently provides: 
	CPUUtilization
	DiskReadBytes
	DiskReadOps
	DiskWriteBytes
	DiskWriteOps
	NetworkIn
	NetworkOut
Thresholds - warning, alarm, and critical 

For authentication against the AWS system, this plugin receives the 
Amazon credentials for the account that launched the AMI on stdin.
The credentials arrive via stdin instead of being passed in as
command-line arguments because of the security concern - otherwise a ps
would show the credentials to any casual user logged into the system.
  
Example: To invoke this script from the command line, enter this line, 
substituting your values for the aws_access_key_id, aws_secret_access_key, 
and aws_ami_id: 

echo "aws_access_key_id aws_secret_access_key" | ./awscloudwatch.py aws_ami_id CPUUtilization 50 75 95

This plugin heavily utilizes the boto framework. The source code should
be downloaded from the boto site (link below) and placed in a folder 
named "boto" in the same directory. For more info see:

BOTO: 
An integrated interface to current and future infrastructural services
offered by Amazon Web Services. http://code.google.com/p/boto/
'''
 
# Copyright (c) 2009-2011 Dartware, LLC
# Licensed under the MIT License, http://www.opensource.org/licenses/mit-license.php
# If you find this code useful, please retain a link back to http://www.intermapper.com

# Original version, August 2009
# Updated to handle different OS Platforms; 
#	tweaked error codes/responses; 
#	enhanced return codes, etc 11Mar2010 -reb
# Minor tweaks for publication 31May2010 -reb
# Changed to use IM 5.3.2 "input" <command-line> capability 22Jul2010 -reb 
# Tweaked comments 9Mar2011 -reb
# Updated command-line example to include echo of two access_keys 15Jun2011 -reb
# Updated to request average for the minute ending one minute ago. This seems to
#	solve the problem of sporadic responses. If you ask for info right up to "now"
#	it seems that CloudWatch won't always have prepared that time interval's data
#	and thus it sometimes returns an empty response. 17 Jun 2011 -reb
# Changed AWS query to retry once if the returned response is empty.
# 	Refactored: Fewer global variables, fewer param's passed around needlessly.
# 	get_path_to_tools_dir() and get_file_data() are no longer used because they were
#	only required when AWS credentials were passed in as separate files (not stdin)
#	18Jun2011 -reb
# Updated to append the "boto" folder to sys.path, so that the import will succeed
#	22Oct2012 -reb

import datetime
import sys
import os
import platform
import time

wd = os.getcwd()
sys.path.append(os.path.join(wd ,"boto"))
# print sys.path
import boto
from boto.exception import BotoServerError

#The following constants are program exit codes that we use within the InterMapper Plugin. 
DOWN   		=4
CRITICAL	=3 
ALARM		=2 
WARN		=1 
OKAY		=0

#global variables

debug = False							# set this to True or False	

'''
Return the path to the InterMapper Settings/Tools directory (including trailing separator) 
'''
def get_path_to_tools_dir():
	osString = platform.platform(aliased=1, terse=1); # get the OS representation
	#print osString

	if (osString.startswith("Darwin")):
		dir = "/Library/Application Support/InterMapper Settings/Tools/" # MacOS X
	elif (osString.startswith("Window")):
		dir = "c:\\Program Files\InterMapper\InterMapper Settings\Tools\\" # Windows
	else:
		dir = "/var/local/InterMapper_Settings/Tools/" # Unix/Linux
	if debug:
		print "Tools Directory is at: %s" % dir
	return dir
    

'''
All returns - good or bad - pass through this routine. 
'''
def write_exit_info(status, condition):
# 	if (conn != None):
# 		conn.close()						# close connection if needed
# 		if debug:
# 			print "Closing Connection!"
	sys.stdout.write(condition)				# output the condition string to stdout
	sys.exit(status)						# return the desired exit status

'''
The usage method prints out the proper arguments that should be passed to this plugin. 
'''

def usage():
	exit_string = "\{ $error := 0 }Usage: %s [<Parameters>]\n" % (os.path.basename(sys.argv[0])) 
	exit_string = exit_string +\
             "  Required:\n" +\
             "  ec2InstanceID\n" +\
             "  metricName\n" +\
             "  warn_threshold\n" +\
             "  alarm_threshold\n" +\
			 "  critical_threshold\n" 	
	write_exit_info(CRITICAL, exit_string)

'''
get_file_data is currently used to read the contents of a file into a variable. 
'''
def get_file_data(file_name):
	try:
		file_path 			= get_path_to_tools_dir() + file_name
		f                   = open(file_path, "r") 
		file_data           = f.read()
		f.close()
	except:
		write_exit_info(DOWN, '\{ $bogus := "[n/a]" }Couldn\'t open file "%s"\n' % (file_name) )

	return file_data
	

'''
Calculate_threshold determines the program exit code based on the 
specified thresholds (passed in as strings).
'''
def calculate_threshold(data, warn_thresh, alarm_thresh, crit_thresh):
	if debug: 
		print 'starting method calculate_threshold with data: %s' % data
	
	if data >= float(crit_thresh):
		returnval = CRITICAL
	elif data >= float(alarm_thresh):
		returnval =  ALARM
	elif data >= float(warn_thresh):
		returnval =  WARN
	else:
		returnval =  OKAY

	if debug:
		print 'Reading is: %s; return code is  %s' % (data, returnval)
	return returnval

'''
Get data from AWS:
Issue the get_metric_statistics() call. 
Handle any exceptions; rerun the query if no results come back the first time. 
Return the data_list from AWS exit directly from the program with the proper status.
'''
def get_aws_data_list(interval, metric, service, metrictype, instance_id, conn):

	# Ask for data from two minutes ago until a minute ago
	end_time   =  datetime.datetime.utcnow() - datetime.timedelta(minutes=1)
	start_time =  end_time - datetime.timedelta(minutes=1)

	if debug: 
		print 'start time is: %s' % start_time
		print 'end time is %s' % end_time	

	for i in [1, 2]:		# Issue the query twice if needed, using same time stamps each time
		try:
			data_list = conn.get_metric_statistics(interval, start_time, end_time, metric,'AWS/EC2','Average', instance_id)
		except BotoServerError, e:
			if debug:
				print 'status=', e.status
				print 'reason=', e.reason
				print 'body=', e.body
				print 'request_id=', e.request_id
				print 'error_code=', e.error_code
				print 'error_message=', e.error_message
			write_exit_info(DOWN, '\{ $%s := "[n/a]" }Got error from CloudWatch - %s\n' % (metric, e.error_message) )
		if data_list != []:						# break out of the loop if we get data back
			break
#		elif(i == 1):
#			print "***** Retrying... *****"  	# and loop 
#			time.sleep(0.1)
#			end_time   =  end_time - datetime.timedelta(seconds=1)
#			start_time =  start_time - datetime.timedelta(seconds=1)

	if debug:
		print data_list

# this next case is debugging code to see if there's ever a successful retry
	if (i==2 and data_list != []):			# debugging code to test if we ever have a successful retry
#		print "===== SUCCESS ====="			
		write_exit_info(WARN, '\{ $%s := "[n/a]" }Had to retry, but got data second time\n' % (metric) )
	if (data_list == []):			# even after a retry, no data...
		write_exit_info(CRITICAL, '\{ $%s := "[n/a]" }No data returned for InstanceID "%s"\n' % (metric, instance_id[u'InstanceId'])) #  time.time()

	return data_list	
	
'''
Make call to Amazon CloudWatch:
Connect using AWS Credentials
Send query to AWS and retrieve results
Parameters:
metric: This is the metric to measure (see CloudWatch Docs For Available metrics)
instance_id: This is the InstanceId to the ec2 instance to measure. 
aws_access_key_id and aws_secret_access_key: are the credentials.
Returns a tuple: (the actual reading, the units for that reading)
'''
def get_metric_data(metric, instance_id, aws_access_key_id, aws_secret_access_key):

# Make a connection to the AWS server system - always seems to return a conn, even if bad keys...
	if debug:
		conn = boto.connect_cloudwatch(aws_access_key_id, aws_secret_access_key, debug=2)
	else:
		conn = boto.connect_cloudwatch(aws_access_key_id, aws_secret_access_key)		
	if (conn == None):
		write_exit_info(DOWN, '\{ $%s := "[n/a]" }Couldn\'t connect to CloudWatch - this is bad.\n' % (metric) )
	
# Get the information from AWS. Handle exceptions and retries when necessary. Only returns if data_list is good.
	data_list = get_aws_data_list(60, metric,'AWS/EC2','Average', instance_id, conn)
		
# Otherwise, data came through just fine
	data = data_list[0]
	reading = data[u'Average']        	# the desired reading
	units   = data[u'Unit']       		# and the units of measure
	
	if debug:
		print 'The Average for %s is %s %s' % (metric, reading, units)

	return (reading, units)	

def main(argv=None):
	
	#get all of the command line argument
	args = sys.argv[1:]
	if len(args) < 5:
		usage()
	
# Read the stdin file which contains access-key-id & secret-access-key, space-separated

	f = sys.stdin							# open stdin
	stdinstr = f.readline().strip()			# get the line & remove leading & trailing whitespace
	keylist = stdinstr.split()				# split the two strings
	if (len(keylist) != 2):					# bail if not two entries
		write_exit_info(CRITICAL, '\{ $error := "[n/a]" }Need both Access_key_ID and Secret_access_key \n' )
	aws_access_key_id     = keylist[0].strip()
	aws_secret_access_key = keylist[1].strip()

# 	aws_access_key_id     = "?????"     	# or substitute your own info when debugging
# 	aws_secret_access_key = "?????"
	
	instance_id			  = args[0].strip()
	metric			      = args[1].strip()
	warn_thresh		      = args[2].strip()
	alarm_thresh		  = args[3].strip()
	crit_thresh	          = args[4].strip()
	
	if debug:
		print "These are the arguments passed from InterMapper: %s" % str(args)
		
	if (instance_id == ""):		# bail if empty
		write_exit_info(CRITICAL, '\{ $error := "[n/a]" }InstanceID must not be empty\n' )

# Get the data from AWS
	instance_list         = {'InstanceId' : instance_id }
	(reading, units) = get_metric_data(metric, instance_list, aws_access_key_id, aws_secret_access_key) 	

# Compute the proper return status
	exit_code = calculate_threshold(reading, warn_thresh, alarm_thresh, crit_thresh)	
     
# Return the proper info from the plugin
#	condition_string = '\{ $%s := \"%s\" }%s is %s %s %s\n' % ( metric, reading, metric, reading, units, exit_code ) # debug output to show exit code as well.
	condition_string = '\{ $%s := \"%s\" }%s is %s %s   \n' % ( metric, reading, metric, reading, units )
	write_exit_info(exit_code, condition_string)
	
if __name__ == "__main__":
	main()
