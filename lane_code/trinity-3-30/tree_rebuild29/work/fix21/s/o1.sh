X=/project/community/jjyeung/okh7/x_22c714e1
ls -la $X/ | head -40
sha256sum $X/jn7.sh $X/jn6.sh 2>&1
wc -c $X/jn7.sh
echo BEGIN_JN7; base64 -w0 $X/jn7.sh; echo; echo END_JN7
