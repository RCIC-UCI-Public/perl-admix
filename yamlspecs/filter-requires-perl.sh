#! /bin/bash
#
# remove requirements for perl 
#
# using beow gives erroneous perl(x) lines
# /usr/lib/rpm/perl.req $* | sed  \

/usr/lib/rpm/find-requires $* | sed  \
    -e '/perl(s)/d' \
    -e '/perl(unicore::Name)/d' \
    -e '/perl(VMS::Stdio)/d' \
    -e '/perl(VMS::Filespec)/d' \
    -e '/perl(Mac::InternetConfig)/d' \
    -e '/perl(Mac::BuildTools)/d' 
