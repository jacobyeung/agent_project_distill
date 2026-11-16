cd /scratch/jjyeung/orch_n30/review_h1kit/work/kit
O=/scratch/jjyeung/orch_n30/review_h1kit/out
mkdir -p $O
bash cpu.sh -m pytest -p no:cacheprovider -p tests.reader_plugin --basetemp "$PWD/tmp/rv_final" tests/test_cli.py tests/test_r0.py tests/test_eval.py tests/test_trainer.py tests/test_stop.py tests/test_rows.py tests/test_own_forward.py -q > $O/pytest_all.log 2>&1; echo "exit $?" >> $O/pytest_all.log
bash cpu.sh -m unittest tests.test_trainer tests.test_stop tests.test_rows tests.test_own_forward tests.test_r0 -v > $O/unittest.log 2>&1; echo "exit $?" >> $O/unittest.log
bash cpu.sh tests/patch_composition.py > $O/patch_comp.log 2>&1; echo "exit $?" >> $O/patch_comp.log
bash cpu.sh tests/faithful_patch_proof.py > $O/faithful_proof.log 2>&1; echo "exit $?" >> $O/faithful_proof.log
bash cpu.sh tests/first_step.py --tree "$PWD/tree" --out $O/off_h1.json > $O/first_step.log 2>&1; echo "exit $?" >> $O/first_step.log
bash cpu.sh tests/compare_off.py --b $O/off_h1.json --out $O/off_identity.json > $O/compare_off.log 2>&1; echo "exit $?" >> $O/compare_off.log
echo ALLDONE > $O/DONE
