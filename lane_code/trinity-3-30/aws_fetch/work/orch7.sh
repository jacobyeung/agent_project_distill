C=/project/community/jjyeung/distill/okit/in/cr
cd $C
ls -la vxm_m4_build | head; sha256sum vxm_m4_build/receipt.json 2>&1
tar tvf rt_b8b60bcef027.tar | head -30
for m in $(tar tf rt_b8b60bcef027.tar | grep -E 'receipt.json$|rows.sqlite$'); do echo "$(tar xOf rt_b8b60bcef027.tar $m | sha256sum | cut -c1-64) $m"; done
echo B64V; base64 -w0 vxm_m4_build/receipt.json; echo
R=$(tar tf rt_b8b60bcef027.tar | grep -E 'r16/receipt.json$' | head -1); echo "B64R16 $R"; tar xOf rt_b8b60bcef027.tar "$R" | base64 -w0; echo
