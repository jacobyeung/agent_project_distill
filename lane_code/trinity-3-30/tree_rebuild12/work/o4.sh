X=/project/community/jjyeung/okh7/x_22c714e1/q; wc -c $X/b/z.py; n=$(grep -n '^def resolve' $X/b/z.py | cut -d: -f1); echo n=$n; sed -n "${n},$((n+70))p" $X/b/z.py | cut -c1-330
cat /project/community/jjyeung/okh7/h_6ed2c7aa/m400/step.1795082288.log; cat /project/community/jjyeung/okh7/h_6ed2c7aa/m400/h.out
