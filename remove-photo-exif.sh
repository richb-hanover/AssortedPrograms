#! /bin/bash
# 
# Remove id info from image
# 

# First remove exif info
exiftool -all= real-file.png  -o clean-file.png

# Then change date to midnight, 1 Jan 1970
touch -t 197001010000.00 clean-file.png
