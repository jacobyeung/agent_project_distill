W=/project/community/jjyeung/okh7/e6fc152498; cd $W; cat b.done 2>/dev/null
awk '{print $6}' g1.list | grep -E '^m/ap/19252904/e/lib/python3.12/site-packages/[^/]+/?$' | sed 's,.*/site-packages/,,' | tr '\n' ' '
