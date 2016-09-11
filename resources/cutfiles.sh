#!/bin/bash

# Cuts each word file up into easier to test pieces, but does so by cutting out every nth line:
for f in ordalisti.algeng.sorted.txt ordalistimax15.sorted.txt; do
    awk 'NR % 100 == 0' $f > $f.cut
    mv $f.cut $f
done

