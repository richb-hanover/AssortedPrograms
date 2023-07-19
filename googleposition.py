#!/usr/local/imdc/core/python/bin/imdc -OO 
# The line above is required to run as an IMDC plugin

# GooglePosition.py 
# Scan Google output for a particular search string 
# Return the position of the desired listing on the results page.
# 24 Nov 2008 -reb
# 07 Nov 2011 Adjusted pattern to look for <li class="g"> because Google stopped returning <!--m-->

##### THIS IS THE TEST LINE #####
# This should have an HTML comment between "..." "<!-- html comment -->"

import os
import re
import sys
import getopt
import urllib
import urllib2
import htmllib

# httplib.HTTPConnection.debuglevel = 1 # force debugging....

# options are: hostName searchString

try:
    opts, args = getopt.getopt(sys.argv[1:], "")
except getopt.GetoptError, err:
    searchString = "getopt error %d" % (err)

hostName = args[0]
# searchString = args[1]
# print hostName

# Read the stdin file which contains the search String
f = sys.stdin							# open stdin
searchString = f.readline().strip()		# get the line & remove leading & trailing whitespace
# print searchString

#hostName = "dartware.com"
#searchString = "network monitoring software"
userAgent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:12.0) Gecko/20100101 Firefox/12.0"
# googleString = "http://www.google.com/search?site=webhp&source=hp&q=%s&aq=f&aqi=g10"
googleString = "http://www.google.com/search?num=50&hl=en&site=&source=hp&q=%s&aq=fas_q=%s&as_epq=&as_oq=&as_eq=&as_nlo=&as_nhi=&lr=&cr=&as_qdr=all&as_sitesearch=&as_occt=any&safe=off&tbs=&as_filetype=&as_rights="

#pat = '''< !--m-->.*?(http.*?)"'''
#pat = '''<li class="g">.*?(http.*?)"'''
#pat = pat.replace(" ","")			# Crock to avoid HTML comment replacement in tool section...
pat = '''<h3 class="r".*?<cite>(.*?)</cite>'''
anchor_pat = re.compile(pat)
search_pat = re.compile(hostName)

# print pat
# print anchor_pat

# fileName = '/Users/richb/Desktop/NetworkMonSW-on-google.html'
# buf = open(fileName).read()

##class AppURLopener(urllib.FancyURLopener):
##    version = userAgent 
##
##urllib._urlopener = AppURLopener()
##
##theURL = googleString%urllib.quote_plus(searchString)
### print theURL
##buf = urllib.urlopen(theURL).read()

qSearch = urllib.quote_plus(searchString)
googleString = googleString % (qSearch, qSearch)

try:
    request = urllib2.Request(googleString)
#    print googleString 
    opener = urllib2.build_opener()
    request.add_header('User-Agent', userAgent)
    buf = opener.open(request).read()
except urllib2.URLError, reason:
    print "\{ $pos := '%s', $url := '%s' } %s" % (51, "", "Can't access server")
    # print "\{ $n1 := \"/\", $v1 := 93845, $n2 := \"/dev\", $v2 := 0, $n3 := \"/.vol\", $v3 := 0 } DISK CRITICAL - free space"

    sys.exit(4)  # make it look down
    
logfile = open('google-results.html', 'w') 
logfile.write(buf) 
logfile.close()
 
i = 0
for href in anchor_pat.findall(buf):
    p = re.compile('<.*?>')					# remove html tags from the URL
    href=p.sub('', href)
    i = i+1
#    print  "*** %d | %s \r\r" % (i , href)
    if (search_pat.search(href, 1)): 
        retstring = "Found '%s' at position %d" % (searchString, i)
        returl = href
        retval = i      # chartable value is its position
        if (i <= 10):
            retcode = 0 # set it to OK status
        elif (i <= 20):
            retcode = 1 # set it to warning status
        elif (i <= 30):
            retcode = 2 # set to alarm status
        else: 
            retcode = 3 # set it to critical status
        break
else:
    retstring = "Not Found - '%s'" % (searchString)
    returl = "--"
    retval = 51         # put it at end
    retcode = 3         # set to critical status

print "\{ $pos := '%s', $url := '%s' } %s" % (retval, returl, retstring)
# print "\{ $n1 := \"/\", $v1 := 93845, $n2 := \"/dev\", $v2 := 0, $n3 := \"/.vol\", $v3 := 0 } DISK CRITICAL - free space"

sys.exit(retcode)
