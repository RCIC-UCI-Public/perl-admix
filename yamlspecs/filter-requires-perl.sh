#! /bin/bash
#
# remove requirements for perl 
# /usr/lib/rpm/find-requires $* | sed -e '/perl(Math::Random)/d' | sed -e '/^[[:space:]]*$/d' | sed -e '/^#/d'

#/usr/lib/rpm/perl.req $* | sed  \
/usr/lib/rpm/find-requires $* | sed  \
    -e '/perl(s)/d' \
    -e '/perl(unicore::Name)/d' \
    -e '/perl(VMS::Stdio)/d' \
    -e '/perl(VMS::Filespec)/d' \
    -e '/perl(Mac::InternetConfig)/d' \
    -e '/perl(Mac::BuildTools)/d' 
