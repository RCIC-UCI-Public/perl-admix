use strict;
use warnings;
use 5.010;
 
#use YAML qw< Dump Bless>;
use YAML::XS;
use MetaCPAN::Client;

my ($name) = @ARGV;
my $mcpan = MetaCPAN::Client->new;
my $dist;

# Perl name notation
# #     Aaa::Bbb  for module 
# #     Aaa-Bbb   for distribution
#
# # check if the argument was a module name
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
