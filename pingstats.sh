#!/bin/bash

# pingstats.sh - Script to start pinging a host and
# produce summary of the response times after receiving a Ctl-C

# Usage: sh pingstats.sh [ host name/ip to ping ]

# If there is an option, use it as the name/address to ping
# Default is gstatic.com

# Copyright (c) 2014 - Rich Brown
# GPLv2


# Create temp file for ping results
PINGFILE=`mktemp /tmp/measurepings.XXXXXX` || exit 1

function clean_up {		# called when Ctl-C is pressed
# clean_up() {			# Use this line to declare the clean_up() function in ash, the CeroWrt shell.
	
	# Process the ping times, and summarize the results
	# grep to keep lines that have "time=", then sed to isolate the time stamps, and sort them
	# awk builds an array of those values, and prints first & last (which are min, max) 
	#	and computes average, the median, and the 10th and 90th percentile readings
	grep "time=" < $PINGFILE | sed 's/^.*time=\([^ ]*\) ms/\1/' | sort -n | \
	awk '{ arr[NR]=$1; sum+=$1; }END \
		 { if (NR%2==1) med=arr[(NR+1)/2]; else med=(arr[NR/2]+arr[NR/2+1])/2; \
			pc10="-"; pc90="-"; \
			if (NR>=10) { ix=int(NR/10); pc10=arr[ix]; ix=int(NR*9/10);pc90=arr[ix]; }; \
			printf("\nMin: %4.3f  10pct: %4.3f  Median: %4.3f  Avg: %4.3f  90pct: %4.3f  Max: %4.3f  Num pings: %d\n", arr[1], pc10, sum/NR, med, pc90, arr[NR], NR )\
		 }'

	# Perform program exit housekeeping
	# NB: Ctl-C stops the associated background ping job
	rm $PINGFILE
	exit
}

trap clean_up SIGHUP SIGINT SIGTERM

PINGHOST="gstatic.com"

if [ $# -ne 0 ]; then
	PINGHOST=$1
fi

ping $PINGHOST > $PINGFILE &

echo "Pinging $PINGHOST... Press Ctl-C to summarize results "
wait

#! /bin/sh
# Take file of pings time readings, compute & display min/max/avg
# Found awk scripts on: 
#	http://blog.damiles.com/2008/10/awk-calculate-mean-min-and-max/
#	http://unix.stackexchange.com/questions/13731/is-there-a-way-to-get-the-min-max-median-and-average-of-a-list-of-numbers-in
# Found clean_up function on: 
#	http://linuxcommand.org/wss0160.php
