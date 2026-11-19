T=/scratch/jjyeung/orch_n30/n_review/tree/student_pilot
grep -n "def single_image_row" -A14 $T/carrier_c1_data.py
grep -n "READOUT_TARGET *=" $T/*.py | head
