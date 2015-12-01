#!/bin/bash
branch=`git branch | grep "^*" | awk '{ print $2 }'`
echo "You're on branch: $branch"
python dawgbuilder.py | tee ./resources/$branch.log
cp ./resources/ordalisti.text.dawg ./resources/ordalisti.text-$branch.dawg
cp ./resources/algeng.text.dawg ./resources/algeng.text-$branch.dawg

