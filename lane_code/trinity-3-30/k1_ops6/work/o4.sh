export TZ=UTC
D=/project/community/jjyeung/distill/okit/in/cr
stat -c '%n %s %y' $D/436d1d64673f.p00 $D/9b9e03337df5.p00 $D/c449bbe907be.p00
echo "--- heads.json content"
cat $D/436d1d64673f.p00; echo
echo "--- sha of heads.json"; sha256sum $D/436d1d64673f.p00
echo "--- sinfo"; sinfo -s 2>&1 | head -20
echo "--- df project"; df -h /project/community 2>&1 | tail -1
echo "--- squeue me"; squeue -u $USER -o '%.10i %.9P %.30j %.2t %.10M %.10l %.20S %R' | head
