X=/project/community/jjyeung/okh7/x_22c714e1; wc -c $X/j/173673.log $X/j/173673.err; grep -v "KITX_OK\|archive members verified\|staged$" $X/j/173673.log | grep -n "" | tail -60 | cut -c1-400
