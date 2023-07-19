#!/bin/perl
#
# Test SNMP querier 
#
# http://www.ugcs.caltech.edu/~goldstei/proj/NetQuery/mibdump

#use strict;
use SNMP::MIB::Compiler;

# make this do more stuff later
$ARGV[0] || die "usage: mibdump infile\n";

my $mib = new SNMP::MIB::Compiler;
my $base = '/home/goldstei/src/net-query';


$mib->add_path("$base/mib/v2");
$mib->add_extension('','.mib','.my');
$mib->repository("$base/mib/v2");
$mib->{'make_dump'} = 1;
$mib->{'use_dump'} = 1;
$mib->{'do_imports'} = 1;
$mib->{'accept_smiv2'} = 1;
$mib->{'accept_smiv1'} = 1;
$mib->{'allow_underscore'} = 1;
$mib->{'allow_lowcase_hstrings'} = 1;
$mib->{'allow_lowcase_bstrings'} = 1;


$mib->compile($ARGV[0]) || die "Error when compling $ARGV[0]\n";

