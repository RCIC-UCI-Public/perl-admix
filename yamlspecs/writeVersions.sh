#!/bin/bash

if [[ $# -ne 1 ]]; then
    echo "Pass as a first directory with yaml files"
    exit 1
fi

DIR=$1
yamls=`ls $DIR | grep yaml | grep -v baseline`
for i in $yamls; 
do
    ver=`grep version: $DIR/$i | sed 's/version://' | sed 's/"//g'`
    name=`basename $i .yaml`
    echo $name $ver | awk '{printf "%-28s %s\n", $1,$2}' 
done
