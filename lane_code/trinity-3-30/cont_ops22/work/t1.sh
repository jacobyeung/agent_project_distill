cd /scratch/jjyeung/orch_n30/cont_ops21_c/hrem
for t in test_hrem.py test_steps_hrem.py test_runtime_hrem.py; do echo "== $t"; timeout 900 /scratch/jjyeung/envs/p1cpu/bin/python -B $t 2>&1 | tail -c 300; echo " rc=$?"; done
B=$(/usr/bin/python3 -c 'import json; print(json.load(open("TEST_RESULTS.json"))["evidence"]+"/build/BUILD.json")')
echo "== guards"; timeout 600 /usr/bin/python3 -B test_guards_hrem.py --build "$B" 2>&1 | tail -c 300; echo
/usr/bin/python3 -B verify_hrem.py >/dev/null && echo VERIFY_OK
test -e run544 && echo RUN544_EXISTS || /usr/bin/python3 configure_hrem.py --parent /project/community/jjyeung/okh7/a15_cot_apdc863c3e6b41d --stage 813f42db/c21h544r --step 544 --out run544
ls -la run544; sha256sum run544/*; grep -c FREE_GIB run544/*.sh
