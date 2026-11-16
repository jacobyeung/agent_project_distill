set +e
export TZ=UTC
C=/project/community/jjyeung
cat /home/jjyeung/okit/fetch_home.sh; echo; cat /home/jjyeung/okit/cr/ofetch.sh; echo
echo "==== official_reads"; cd $C/official_reads; ls -la . bin plans runs scores tree vview logs 2>&1 | head -120; cat status.json | head -50; cat VCHECK.json | head -40
echo "==== cp4tk_f17"; ls -la $C/cp4tk_f17
