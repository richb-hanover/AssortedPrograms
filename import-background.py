#####
#
# This Python program retrieves a URL from the wallpaperURL website, and then
#    imports it (using HTTP POST) into a InterMapper server's "Backgrounds" 
#    folder as a file named "bgwallpaper.jpg".
#
# The program retrieves an image from wallpaperURL and imports it every 20 minutes.
#
# A temporary copy of the image is saved in /tmp/wallpaper.jpg. This needs to be adjusted
#    for Windows systems.
#
#####

# Program to retrieve background images from CodeFromThe70s.org
# One single thread that: 
#   - retrieves image via HTTP. Runs every 20 minutes for politeness to the CodeFromThe70s server
#   - and then uses IM HTTP API to push the image into the Backgrounds folder

# not much error handling: os errors will halt the program I'm pretty sure. Uses a lock to mediate access
# to the graphic being retrieved/imported.
# 30 Nov 2010 -reb
# 07 Dec 2010 -reb
# 23 Jun 2011 Pruned out lots of test/debug code ... -reb
#  3 Jul 2011 Added back the 'importer' routine -reb

# http://www.gossamer-threads.com/lists/python/python/652793?page=last
import threading
import time
import os
import urllib

# This URL returns a JPEG form the CodeFromThe70s server when it is given a UTC timestamp at the end, like this ...&utc=129046401
wallpaperURL = 'http://www.codefromthe70s.org/cgi/desktopearthgen.exe?width=1280&height=768&center=5&bars=1&clouds=1&utc=%s'
#wxmapURL     = 'http://image.weather.com/images/maps/current/curwx_600x405.jpg'

# These URLs do the import into InterMapper
curlwallpaper = 'curl -k -s --data-binary "@/tmp/wallpaper.jpg" https://127.0.0.1/~files/icons/Backgrounds/bgwallpaper.jpg'
#curlicon      = 'curl -k -s --data-binary "@time-icon.png"      https://127.0.0.1/~files/icons/Default/time-icon.png'
#curlwxmap     = 'curl -k -s --data-binary "@wxmap.jpg"          https://127.0.0.1/~files/icons/Backgrounds/wxmap.jpg'

#imgmgktime = "convert wallpaper.jpg -fill white -undercolor '#00000080' -gravity SouthEast -annotate +0+5 ' %s ' wallpaper-time.jpg"
#imgmgkicon = "convert -background lightblue -fill blue -pointsize 36 label:'%s' time-icon.png"


def repeat(event, every, action):
    while True:
        action()
        event.wait(every)
        if event.isSet():
            break

# Thread to send the timestamped wallpaper image & icon to IM via HTTP
def importer():
    aDate = time.strftime("%Y-%b-%d_%H-%M-%S",time.localtime())
    aTime = time.strftime("%H:%M")
    print "HTTP POST image to IM at %s..." % (aDate)

# generate the updated icon file
#    retcode = os.system(imgmgkicon % aTime) 

    imgLock.acquire()
    retcode = os.system("%s  > /dev/null" % (curlwallpaper)) # send wallpaper
#    retcode = os.system("%s  > /dev/null" % (curlicon))      # send icon
#    retcode = os.system("%s  > /dev/null" % (curlwxmap))     # send weathermap
    imgLock.release()

# Thread to retrieve Desktop Earth image, and then import it into InterMapper via HTTP
def retriever():
    aDate = time.strftime("%Y-%b-%d_%H-%M-%S",time.localtime())
    aDateSecs = str(int(time.time()))
    print "Retrieving wallpaper image at %s..." % (aDate)
# Retrieve the image from CodeFromThe70s
# acquire lock for the image file
    imgLock.acquire()
#    print wallpaperURL % aDateSecs
    (fname, hdrs) = urllib.urlretrieve(wallpaperURL % aDateSecs, '/tmp/wallpaper.jpg')
# update the image by adding the time stamp into the lower-right corner of the image using ImageMagick
#    print imgmgkcmd % aDate
#    retcode = os.system(imgmgktime % aDate)

# And do the import into InterMapper
    retcode = os.system("%s  > /dev/null" % (curlwallpaper)) # send wallpaper

    imgLock.release()

# Thread to retrieve weather map and save it
# def retrieveWxMap():
#     aDate = time.strftime("%Y-%b-%d_%H-%M-%S",time.localtime())
#     print "Retrieving weathermap image at %s..." % (aDate)
# Retrieve the image from Weather.com
# acquire lock for the image file
#     imgLock.acquire()
#     (fname, hdrs) = urllib.urlretrieve(wxmapURL, '/home/dartware/Documents/wxmap.jpg')
#     imgLock.release()

# Create the lock to control access to the image
imgLock = threading.Lock()

print "creating thread to retrieve the wallpaper image"
ev1 = threading.Event()
retrievalThread = threading.Thread(target=repeat, args=(ev1, 60*20, retriever))
print "starting it"
retrievalThread.start()

# print "creating thread to retrieve the weather map image"
# ev2 = threading.Event()
# retrievalThread2 = threading.Thread(target=repeat, args=(ev2, 60*5, retrieveWxMap))
# print "starting it"
# retrievalThread2.start()

print "creating thread to HTTP POST it into InterMapper"
ev = threading.Event()
importThread = threading.Thread(target=repeat, args=(ev, 60.0, importer))
print "starting it"
importThread.start()

print "starting main thread; end in 24 hours"

try:
    time.sleep(60*60*24) # stop after 24 hours
except KeyboardInterrupt:
    print " Keyboard interrupt"
else:
    print "setting event because time has run out"
ev.set()
ev1.set()
# ev2.set()

print "waiting for threads to finish"
importThread.join()
retrievalThread.join()
print "quit"
