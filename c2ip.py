'''
Convert PQS ip2c.txt files of this form:

16777214,??
16777471,AU
16778239,CN
16779263,AU
16781311,CN
16785407,JP
16793599,CN
16809983,JP
...

to the same data followed by the real IP address...

16777214,??,0.255.255.254
16777471,AU,1.0.0.255
16778239,CN,1.0.3.255
16779263,AU,1.0.7.255
16781311,CN,1.0.15.255
16785407,JP,1.0.31.255
16793599,CN,1.0.63.255
16809983,JP,1.0.127.255
...

This file currently is produced by a script on the Dartware 
vweb2.dartwre.com server and is written to this URL:
http://download.dartware.com/ip2c/ip2c.txt

5Oct2012 -reb
'''

import socket, struct, sys

def to_string(ip):                  # stolen from some place on the internet
  "Convert 32-bit integer to dotted IPv4 address."
  return ".".join(map(lambda n: str(ip>>n & 0xFF), [24,16,8,0]))
    
def main(argv=None):
    f = sys.stdin
    while True:
        line = f.readline().strip()
        if line == "":
            break
        num, country = line.split(",")
        quad = to_string(long(num))
        print num + "," + country + "," + quad

if __name__ == "__main__":
    sys.exit(main())
    
