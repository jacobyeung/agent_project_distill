set -u
D=/project/community/jjyeung/okh7/3fd71adb; C=/project/community/jjyeung/distill/okit/in/cr
umask 077; cd $D
while IFS=$'\t' read -r n s u; do
  r=$(curl -s -o up_$n.json -w '%{http_code} %{size_upload} %{time_total}' --limit-rate 40M -X PUT -H "Content-Length: $s" --upload-file $C/$n.tar "$u")
  echo "$n $r"; head -c 600 up_$n.json | tr -d '\n'; echo
done < sess.tsv
