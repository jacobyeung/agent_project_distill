P=/project/community/jjyeung/okh7/a15_cot_apda6f7936c1779/a
cd $P && tar cf - 4.py 5.py 6.py 7.py export.json 10.json | base64 -w0; echo
