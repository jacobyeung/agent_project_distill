T=/scratch/jjyeung/orch_n30/n_review/tree/student_pilot
sed -n 470,580p $T/carrier_c1.py
echo ====data; sed -n 425,475p $T/carrier_c1_data.py
echo ====run1365; sed -n 1360,1385p $T/carrier_c1_run.py
grep -n "b32359ce\|0b95850a\|a2v3\|a3v2" /scratch/jjyeung/orch_n30/sb_framepool/out/FPJOIN_REPORT.md | head -10
