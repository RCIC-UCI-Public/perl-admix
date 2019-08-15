use strict;
use warnings;
use 5.010;
 
use YAML::XS;
# next line makes no difference, keep for refrence 
#$YAML::XS::LoadBlessed = 1 ;
use MetaCPAN::Client;

my ($name) = @ARGV;
my $mcpan = MetaCPAN::Client->new;
my $dist;

# Perl name notation
#    Aaa::Bbb  for module 
#    Aaa-Bbb   for distribution
# check if the argument was a module or a distribution
# TODO: error checking for wrong names
my $module = eval { $mcpan->module( $name ) };
if ($@) { # given distribution name
    say STDERR "processing distro $name";
    $dist = $mcpan->release( $name );
}
else {  # module name
    say STDERR "processing module $name ";
    $dist = $mcpan->release( $module->distribution );
}

say Dump ($dist);
