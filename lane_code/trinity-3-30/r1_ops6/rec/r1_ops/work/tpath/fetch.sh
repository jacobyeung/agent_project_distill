export TZ=UTC
O=/project/community/jjyeung/okh7
cd $O
for K in x_3fdda0fb x_69d2930d; do
  find $K -maxdepth 3 -type f ! -name 'sess.json' ! -path '*/o/*' ! -path '*/runs/*' -printf '%s %p\n' | sort -k2 > /tmp/jjyeung_list_$K.txt 2>/dev/null
done
echo "@@LISTS"
cat /tmp/jjyeung_list_x_3fdda0fb.txt /tmp/jjyeung_list_x_69d2930d.txt | awk '{print $1, $2}' | wc -l
tar czf - $(for K in x_3fdda0fb x_69d2930d; do find $K -maxdepth 3 -type f -size -2000k ! -name 'sess.json' ! -path '*/o/*' ! -path '*/runs/*' ! -name '*.tar' ! -name '*.gz' ! -path '*/__pycache__/*'; done) /tmp/jjyeung_list_x_3fdda0fb.txt /tmp/jjyeung_list_x_69d2930d.txt 2>/dev/null | base64 -w0
