#!/usr/bin/perl

# Usage: perl getinfo.pl ModName|DistName
#        outputs yaml definition of the package or distribution
#        that can be parsed  to get info about dependencies
#        and other values
# Perl name notation
#     Aaa::Bbb  for module 
#     Aaa-Bbb   for distribution

use strict;
use warnings;
use 5.010;
 
use YAML::Dump qw< Dump >;
use MetaCPAN::API;

# enforce sorting of the printed object keys
#use Data::Dumper;
#$Data::Dumper::Sortkeys = 1;
  
my ($name) = @ARGV;
my $mcpan = MetaCPAN::API->new;
my $dist;

# check if the argument was a module name
my $module = eval { $mcpan->module( $name ) };
if ($@) { # given distribution name
    say STDERR "processing distro $name";
    $dist = $mcpan->release( distribution => $name );
}
else {  # module name
    say STDERR "processing module $name distro $module->{distribution}";
    $dist = $mcpan->release( distribution => $module->{distribution} );
}

#say Dumper ($dist);
say Dump ($dist);

