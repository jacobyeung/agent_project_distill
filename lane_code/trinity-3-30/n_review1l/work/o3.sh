X=/project/community/jjyeung/okh7/x_22c714e1
for k in qd c_eb8145adr; do echo "== $k"; (cd $X/$k && find . -type f | sort | xargs sha256sum | cut -c1-16,65- ); done
