#!/bin/bash
#
# Create filters for rewriting perl rpm provides/requires
# Filters are created in the package temp build directory 
# Naming convention: filter-provides-NAME.sh 
#                    filter-requires-NAME.sh
# where NAME is a module name 

# check passed arguments and set variables 
if [ $# -lt 3 ];  then
    exit 0
fi
PKGYAML=$1 # package yaml file
BDIR=$2    # package temp build directory
COMMAND=$3 # command to generate variables

# Run commands to parse the yml file and find directives
PERLVERSION=`$COMMAND --query=versions.perl $PKGYAML` # perl version
NAME=`$COMMAND --query=name $PKGYAML`                 # module name

# default filters
default_perl=" -e 's/perl(/perl_$PERLVERSION(/'"  
default_requires="-e '/perl(Mac::Pasteboard)/d' -e '/perl(Win32::Clipboard)/d' -e '/perl(Win32)/d' $default_perl"
default_provides=$default_perl


createFilter () 
{
    ftype=$1                            # provides or requires
    fname=$BDIR/filter-$ftype-$NAME.sh  # filter file name to write

    # check package yaml for directives
    add=`$COMMAND --query=filter_$ftype $PKGYAML`      
    if [ "x$add" == "xFalse" ]; then # use defauts
        [ $ftype == "requires" ] && add=$default_requires || add=$default_provides
    else # use directives
        if [ $ftype == "requires" ]; then
            add+=$default_perl 
        else
            add1=$default_perl" | sed '$add'"
            add=$add1
        fi
    fi

    # write filter file
    txt="#!/bin/bash
# Rewrite perl rpm $ftype
/usr/lib/rpm/find-$ftype \$* | sed $add"

    echo "$txt" > $fname
    chmod +x $fname
}

createFilter "requires"
createFilter "provides"

