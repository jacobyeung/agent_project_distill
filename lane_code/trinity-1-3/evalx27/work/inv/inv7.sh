set +e
export TZ=UTC
C=/project/community/jjyeung
echo "==== gcloud"; ls -la $C/gcloud; ls -la $C/gcloud/* | head -60
echo "==== find home"; timeout 60 find /home/jjyeung -maxdepth 5 \( -name '*e193c2a3c*' -o -name '*ebe307cf4*' -o -name 'a0n3_000*' -o -name '*mstop*' -o -name '*b8ebab38*' -o -name '*555eb739*' -o -name '*90c2c742*' \) -printf '%y %s %TY-%Tm-%TdT%TH:%TM %p\n' 2>/dev/null
echo "==== find /tmp login"; ls -la /tmp 2>/dev/null | grep jjyeung | head -30
echo "==== find community d3"; timeout 150 find $C -maxdepth 3 \( -name '*e193c2a3c*' -o -name '*ebe307cf4*' -o -name 'a0n3_000*' -o -name '*mstop*' -o -name '*b8ebab38*' -o -name '*555eb739*' -o -name '*90c2c742*' -o -name 'q8' \) -printf '%y %s %TY-%Tm-%TdT%TH:%TM %p\n' 2>/dev/null
echo rc=$?
