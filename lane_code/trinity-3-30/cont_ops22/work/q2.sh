cd /scratch/jjyeung/orch_n30/cont_ops21_c/hrem
echo ===PF; cat -n place_fill_hrem.py
echo ===FV; cat -n fetch_validation.py
echo ===OF; cat -n in/o_fetch_h400.sh
echo ===OFH; cat -n o_fetch_hrem.sh o_place_fill_hrem.sh
echo ===GEN; cat -n generate_scripts_hrem.py
echo ===VER; sed -n 1,60p verify_hrem.py
