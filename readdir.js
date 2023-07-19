// Code to scan files in the /tmp directory, filter out the "netperf logs" and 
// summarize their distribution by time

// Ultimately made its way into the netperf.richb-hanover.com site

var fs = require('fs');
var path = require('path');
var _ = require('underscore');

var t1 = new Date().getTime();
var filelist = fs.readdirSync( "/tmp");
//var filelist = "/tmp/netperfUL.JUjDuo";

var netperflist = _.filter(filelist, function(fname){ return fname.indexOf("netperfUL") == 0 });

var timeList = _.map(netperflist, function(fname) { 
	var mt = fs.statSync(path.join("/tmp", fname)).mtime; 
	return mt.getTime(); 
	});
// timeList = _.sortBy(timeList, function(t) { return t.getTime()});

var lastmin, last5min, lasthour, lastday = 0;
lastmin  = _.filter(timeList, function(ftime) { return ftime > t1-1000*60 }).length;
last5min = _.filter(timeList, function(ftime) { return ftime > t1-1000*60*5 }).length;
lasthour = _.filter(timeList, function(ftime) { return ftime > t1-1000*60*60 }).length;
lastday  = _.filter(timeList, function(ftime) { return ftime > t1-1000*60*60*24 }).length;
t2 = new Date().getTime();

//console.log(timeList);
console.log( lastmin, last5min, lasthour, lastday);
console.log( t2 - t1 + " msec");

console.log("--- second way ---");
filelist = fs.readdirSync( "/tmp");
t3 = new Date().getTime();
var timeList = _.chain(filelist)
	.filter(function(fname){ return fname.indexOf("netperfUL") == 0 })
	.map(function(fname) { 
		var mt = fs.statSync(path.join("/tmp", fname)).mtime; 
		return mt.getTime(); 
		})
	.value();

lastmin  = _.filter(timeList, function(ftime) { return ftime > t1-1000*60 }).length;
last5min = _.filter(timeList, function(ftime) { return ftime > t1-1000*60*5 }).length;
lasthour = _.filter(timeList, function(ftime) { return ftime > t1-1000*60*60 }).length;
lastday  = _.filter(timeList, function(ftime) { return ftime > t1-1000*60*60*24 }).length;
t4 = new Date().getTime();

console.log( lastmin, last5min, lasthour, lastday);
console.log(t4 - t3 + " msec");
