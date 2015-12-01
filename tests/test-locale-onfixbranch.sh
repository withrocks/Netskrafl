#!/bin/bash
branch=fixbranch
python dawgbuilder.py > ./resources/$branch.log
cp ./resources/ordalisti.text.dawg ./resources/ordalisti.text-$branch.dawg
cp ./resources/algeng.text.dawg ./resources/algeng.text-$branch.dawg

