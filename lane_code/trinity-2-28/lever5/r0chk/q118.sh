hostname -s; R=/scratch/jjyeung/orch_n30/b10_reserve; ls $R $R/code $R/out 2>&1 | head -40
grep -n -E 'f41d15aa|division|kit07|A3' $R/code/census.py | cut -c1-300 | head -20
sed -n 1,60p $R/code/test_exclusion.py | cut -c1-250
