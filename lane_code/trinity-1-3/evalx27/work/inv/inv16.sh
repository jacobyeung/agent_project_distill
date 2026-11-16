set +e
export TZ=UTC
C=/project/community/jjyeung
echo "==== harness log"; cat $C/official_reads/logs/harness_o_p1w4m200_vsi_165610.log | head -30
echo "==== driver log"; head -40 $C/official_reads/logs/driver_165610.log
echo "==== plan"; cat $C/official_reads/plans/PLAN_A.json
echo "==== .stage"; ls -la $C/official_reads/.stage $C/official_reads/.stage/* | head -40
echo "==== cp4tk_eval/inputs"; ls -la $C/cp4tk_eval/inputs $C/cp4tk_eval/inputs/* 2>&1 | head -60
echo "==== q7e/stage"; ls -la $C/q7e $C/q7e/stage $C/q7e/stage/distill 2>&1 | head -40
echo "==== changed after 15:32Z"; timeout 60 find /home/jjyeung/okit -maxdepth 4 -newermt '2026-11-15 15:32:00' -printf '%y %s %TY-%Tm-%TdT%TH:%TM:%TS %p\n' 2>/dev/null | head -40; timeout 90 find $C -maxdepth 2 -newermt '2026-11-15 15:32:00' -printf '%y %s %TY-%Tm-%TdT%TH:%TM:%TS %p\n' 2>/dev/null | head -40
echo "==== tmp newest"; ls -lt /home/jjyeung/okit/tmp | head
