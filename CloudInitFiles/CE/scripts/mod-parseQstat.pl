#!/usr/bin/perl -w

use strict;
my @jobids = `qstat -f alice| grep 'Job Id'`;
chomp @jobids;
s/^Job Id: // foreach @jobids;
foreach (@jobids) {
  my ($cput, $wt, $wn, $status);
  foreach (`qstat -f $_`) {
    chomp;
    m/resources_used.cput/ and (undef, $cput) = split /=/;
    m/resources_used.walltime/ and (undef, $wt) = split /=/;
    m/exec_host/ and (undef, $wn) = split /=/;
    m/job_state/ and (undef, $status) = split /=/;
  } 
#  my $eff = seconds($cput)/seconds($wt);
  
  if ($status eq " R")
   {
   my $eff = seconds($cput)/(1+seconds($wt));
   print "$_\t$wn\t\t$wt\t$cput\t$eff";
   print "<-------------" if $eff<0.2;
   print "\n";
   }
}

exit 0;

sub seconds {
  my $string = shift;
  chomp $string;
#  print "--->$string<---\n";
  my $h0=0;
  my $m0=0;
  my $s0=0;
  my ($hrs,$min,$sec) = split /:/,$string;
  return 60*60*($hrs+$h0)+60*($min+$m0)+$sec;
}
