#! /bin/sh
# 
# Shell script to send test emails to Rich's mail server (mail.richb-hanover.com) 
# to ensure those messages are directed properly.
# 

cd "/Users/richb/Documents/src/Assorted Programs"
./swaks.pl --from=richb.hanover@gmail.com --server=mail.richb-hanover.com:25 --header="Subject: Test from Rich" --body @./TestMsg.txt --to=info@richb-hanover.com
./swaks.pl --from=richb.hanover@gmail.com --server=mail.richb-hanover.com:25 --header="Subject: Test from Rich" --body @./TestMsg.txt --to=info@blueberryhillsoftware.com
./swaks.pl --from=richb.hanover@gmail.com --server=mail.richb-hanover.com:25 --header="Subject: Test from Rich" --body @./TestMsg.txt --to=rich.brown@blueberryhillsoftware.com
./swaks.pl --from=richb.hanover@gmail.com --server=mail.richb-hanover.com:25 --header="Subject: Test from Rich" --body @./TestMsg.txt --to=info@thejugglerman.com
./swaks.pl --from=richb.hanover@gmail.com --server=mail.richb-hanover.com:25 --header="Subject: Test from Rich" --body @./TestMsg.txt --to=info@pinnacleproject.info
./swaks.pl --from=richb.hanover@gmail.com --server=mail.richb-hanover.com:25 --header="Subject: Test from Rich" --body @./TestMsg.txt --to=info@lochlymelodge.com

# ./swaks.pl --from=wifi80211@pm.me --server=mail.richb-hanover.com:25  --header="Subject: Test from Rich" --to=info@blueberryhillsoftware.net
# ./swaks.pl --from=wifi80211@pm.me --server=mail.richb-hanover.com:25  --header="Subject: Test from Rich" --to=info@pinnacleproject.net
# ./swaks.pl --from=wifi80211@pm.me --server=mail.richb-hanover.com:25  --header="Subject: Test from Rich" --to=info@pinnacleproject.org

echo "-----"
echo "Six messages sent."
echo ""
