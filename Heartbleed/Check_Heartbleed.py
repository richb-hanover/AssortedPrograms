#!/usr/bin/python2

# Check_Heartbleed.py v0.6
# 18/4/2014

# Quick and dirty demonstration of CVE-2014-0160 by Jared Stafford (jspenguin@jspenguin.org)
# The author disclaims copyright to this source code.

# Modified for simplified checking by Yonathan Klijnsma

# Modified to turn into a Nagios Plugin by Scott Wilkerson (swilkerson@nagios.com)
# Modified to include TLSv1.2 as well as v1.1, defaults to 1.1 (sreinhardt@nagios.com)
# Modified to check all three versions of TLS, dropping out of loop as soon as a vulnerability is found;
#      fixed error in TLS version numbers; must be set in the ClientHello *and* the Heartbeat structure
#      display host name/address, port, and TLS version(s) in Nagios output (rich.brown@blueberryhillsoftware.com)

import sys
import struct
import socket
import time
import select
from optparse import OptionParser

target = None
okstring = ""   # string to accumulate if all is OK, shows result of all three TLS versions
endtime = 0

options = OptionParser(usage='%prog server [options]', description='Test for SSL heartbeat vulnerability (CVE-2014-0160)')
options.add_option('-H', '--host',    type='string',      default='127.0.0.1', help='Host to connect to (default: 127.0.0.1)')
options.add_option('-p', '--port',    type='int',         default=443,         help='TCP port to test (default: 443)')
options.add_option('-v', '--version', type='int',                              help='TLS version to test [v1.x for 0..2] (default: 1)')
options.add_option('-t', '--timeout', type='int',         default=10,          help='Plugin timeout length (default: 10)')
options.add_option('-u', '--udp',     action='store_true',default=False,       help='Use TCP or UDP protocols, no arguments needed. This does not work presently, keep to TCP. (default: TCP)')


# These initialization routines come from hb-test.py by takeshix <takeshix@adversec.com>
# They insert the desired TLS version in the header, the ClientHello, and the Heartbeat
# Original code from: https://gist.github.com/takeshixx/10107280

def hex2bin(arr):
    return ''.join('{:02x}'.format(x) for x in arr).decode('hex')

def build_client_hello(tls_ver):
    client_hello = [
# TLS header ( 5 bytes)
0x16,               # Content type (0x16 for handshake)
0x03, tls_ver,         # TLS Version
0x00, 0xdc,         # Length
# Handshake header
0x01,               # Type (0x01 for ClientHello)
0x00, 0x00, 0xd8,   # Length
0x03, tls_ver,         # TLS Version
# Random (32 byte)
0x53, 0x43, 0x5b, 0x90, 0x9d, 0x9b, 0x72, 0x0b,
0xbc, 0x0c, 0xbc, 0x2b, 0x92, 0xa8, 0x48, 0x97,
0xcf, 0xbd, 0x39, 0x04, 0xcc, 0x16, 0x0a, 0x85,
0x03, 0x90, 0x9f, 0x77, 0x04, 0x33, 0xd4, 0xde,
0x00,               # Session ID length
0x00, 0x66,         # Cipher suites length
# Cipher suites (51 suites)
0xc0, 0x14, 0xc0, 0x0a, 0xc0, 0x22, 0xc0, 0x21,
0x00, 0x39, 0x00, 0x38, 0x00, 0x88, 0x00, 0x87,
0xc0, 0x0f, 0xc0, 0x05, 0x00, 0x35, 0x00, 0x84,
0xc0, 0x12, 0xc0, 0x08, 0xc0, 0x1c, 0xc0, 0x1b,
0x00, 0x16, 0x00, 0x13, 0xc0, 0x0d, 0xc0, 0x03,
0x00, 0x0a, 0xc0, 0x13, 0xc0, 0x09, 0xc0, 0x1f,
0xc0, 0x1e, 0x00, 0x33, 0x00, 0x32, 0x00, 0x9a,
0x00, 0x99, 0x00, 0x45, 0x00, 0x44, 0xc0, 0x0e,
0xc0, 0x04, 0x00, 0x2f, 0x00, 0x96, 0x00, 0x41,
0xc0, 0x11, 0xc0, 0x07, 0xc0, 0x0c, 0xc0, 0x02,
0x00, 0x05, 0x00, 0x04, 0x00, 0x15, 0x00, 0x12,
0x00, 0x09, 0x00, 0x14, 0x00, 0x11, 0x00, 0x08,
0x00, 0x06, 0x00, 0x03, 0x00, 0xff,
0x01,               # Compression methods length
0x00,               # Compression method (0x00 for NULL)
0x00, 0x49,         # Extensions length
# Extension: ec_point_formats
0x00, 0x0b, 0x00, 0x04, 0x03, 0x00, 0x01, 0x02,
# Extension: elliptic_curves
0x00, 0x0a, 0x00, 0x34, 0x00, 0x32, 0x00, 0x0e,
0x00, 0x0d, 0x00, 0x19, 0x00, 0x0b, 0x00, 0x0c,
0x00, 0x18, 0x00, 0x09, 0x00, 0x0a, 0x00, 0x16,
0x00, 0x17, 0x00, 0x08, 0x00, 0x06, 0x00, 0x07,
0x00, 0x14, 0x00, 0x15, 0x00, 0x04, 0x00, 0x05,
0x00, 0x12, 0x00, 0x13, 0x00, 0x01, 0x00, 0x02,
0x00, 0x03, 0x00, 0x0f, 0x00, 0x10, 0x00, 0x11,
# Extension: SessionTicket TLS
0x00, 0x23, 0x00, 0x00,
# Extension: Heartbeat
0x00, 0x0f, 0x00, 0x01, 0x01
    ]
    return hex2bin(client_hello)

def build_heartbeat(tls_ver):
    heartbeat = [
0x18,       # Content Type (Heartbeat)
0x03, tls_ver,  # TLS version
0x00, 0x03,  # Length
# Payload
0x01,       # Type (Request)
0x40, 0x00  # Payload length
    ]
    return hex2bin(heartbeat)

# Common exit point for code paths
def plugin_exit(message, status):
    print message
    sys.exit(status)

# accumulate list of successful tests in case they all succeed
def not_vulnerable(message, status):
    global okstring, versname
    if okstring != "":
        okstring += ", "
    okstring += versname

# recvall - receive length bytes from s, calling select() as needed, looping for specified timeout
def recvall(s, length):
    global target, opts, endtime
    rdata = ''
    remain = length
    while remain > 0:
        rtime = endtime - time.time()
        if rtime < 0:
            return None

        r, w, e = select.select([s], [], [], 1)  # 1 second timeout within the loop
        if s in r:
            try:
                data = s.recv(remain)
            except socket.error:
                plugin_exit('UNKNOWN: No data received from ' + target, 3)

            # Did we reach EOF?
            if data == "":
                return None
            rdata += data
            remain -= len(data)
    return rdata
        
#Receives messages and handles accordingly
def recvmsg(s):
    hdr = recvall(s, 5)
    if hdr is None:
        return None, None, None
    typ, ver, ln = struct.unpack('>BHH', hdr)
    pay = recvall(s, ln)
    if pay is None:
        return None, None, None
 
    return typ, ver, pay

#Prints Nagios style output and exit (if vulnerable)
# or return True if there's more data (false if not)
def check_output(typ, ver, pay):
    global target, opts

    if typ is None:
        not_vulnerable('OK: ' + target + ' - NOT VULNERABLE', 0)
        return False

    # print "Got typ: {}, ver: {}, len(pay): {}".format(typ,ver,len(pay))

    if typ == 24:
        if len(pay) > 3:
            plugin_exit('CRITICAL: ' + target + ' - VULNERABLE', 2)
        else:
            not_vulnerable('OK: ' + target + ' - NOT VULNERABLE', 0)
            return True

    # Alert (21) signals something bad happened, and that the connection is closing
    # This should no longer happen, since it was triggered by TLS version mismatch
    # between ClientHello and the Heartbeat packet
    if typ == 21:
        # not_vulnerable('OK: ' + target + ' - NOT VULNERABLE', 0)
        return True

    #if no type matches
    plugin_exit('UNKNOWN: Response from ' + target + ' (' + str(typ) + ') did not match any known values.', 3)

# Initiates connection and handles initial hello\hb sending
def connect(tlsv):
    global target, opts
 
    if opts.udp:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    else:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    sys.stdout.flush()

    s.settimeout(opts.timeout)

    try: 
        s.connect((opts.host, opts.port))
    except socket.error:
        plugin_exit('UNKNOWN: Connecton to server ' + target + ' could not be established.', 3)

    sys.stdout.flush()

    try:
        s.send(build_client_hello(tlsv))
    except socket.error:
        plugin_exit('UNKNOWN: Error sending hello to ' + target, 3)

    sys.stdout.flush()
    while True:
        typ, ver, pay = recvmsg(s)
        if typ is None:
            plugin_exit('UNKNOWN: Server ' + target + ' closed connection without sending Server Hello.', 3)

        # Look for server hello done message.
        if typ == 22 and ord(pay[0]) == 0x0E:
            break

    sys.stdout.flush()

    hb = build_heartbeat(tlsv)
    try:
        s.send(hb)
    except socket.error:
        plugin_exit('UNKNOWN: Error sending heartbeat to ' + target, 3)

    return s

def main():
    global target, opts, okstring, endtime, versname
    opts, args = options.parse_args()

    tls_range = [0, 1, 2]                           # Default is all TLS versions
    if opts.version != -1 and opts.version != None:
        tls_range = [opts.version]

    for tlsv in tls_range:
        endtime = time.time() + opts.timeout        # end time for this connection

        versname = "1." + str(tlsv)
        target = "{} (port {}, v{})".format(opts.host, str(opts.port), versname)

        s = connect(tlsv)   # Send the ClientHello and if no errors, send Heartbeat

        moredata = True
        while moredata:
            typ, ver, pay = recvmsg(s)
            moredata = check_output(typ, ver, pay)

    okstring = "OK: " + opts.host + " (port " + str(opts.port) + ", TLS v" + okstring + ") - NOT VULNERABLE"
    plugin_exit(okstring, 0)

if __name__ == '__main__':
    main()
