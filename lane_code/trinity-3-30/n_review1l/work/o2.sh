X=/project/community/jjyeung/okh7/x_22c714e1
ls -la $X/o/173912/ | awk '{print $5, $9}' | sort -n | tail -60 | tr '\n' ';'
