O=/project/community/jjyeung/okh7; R=$O/x_22c714e1/o/n10_du3_0925Z.txt
cat > $O/x_22c714e1/o/n10_du3.sh <<'IN'
O=/project/community/jjyeung/okh7
echo "start $(date -u +%FT%TZ)"
echo "== dedup total okh7"; nice -n 19 ionice -c3 du -s -B1M $O 2>/dev/null
for d in r e6fc152498 a15_cot_ap90eaf12c47ba5 a15_cot_apfadf2291c654b a15_cot_apda6f7936c1779 a15_cot_apd296bd1ef61cd i_bb09a77d db3954b2 d9c35d0a probe37845077 i_1be16f28 x_22c714e1/w x_22c714e1/u; do
  echo "== $d (files >= 256M: bytes links mtime path)"; ls -la --time-style=+%FT%H:%MZ $O/$d | head -12
  nice -n 19 find $O/$d -maxdepth 4 -type f -size +256M -printf '%s %n %TY-%Tm-%TdT%TH:%TM %P\n' 2>/dev/null | sort -rn | head -12
done
echo "== jjyeung top level"; ls -la --time-style=+%FT%H:%MZ /project/community/jjyeung | head -60
echo "end $(date -u +%FT%TZ)"
IN
nohup setsid bash $O/x_22c714e1/o/n10_du3.sh < /dev/null > $R.part 2>&1 &
echo "DU3 launched $(date -u +%FT%TZ) -> $R.part"; df -B1 /project/community | tail -1
