#!/bin/bash

# Does two runs of dawgbuilder in a row
set -e

for f in resource1 resource2
do
    time python dawgbuilder.py > resources/lastrun.txt 2>&1
    if [ -d $f ]; then
        rm -rf ./$f
    fi
    cp -r resources $f 
done
