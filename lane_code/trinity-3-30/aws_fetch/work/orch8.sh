C=/project/community/jjyeung/distill/okit/in/cr
cd $C
ls -la | head -40
for t in rt_81d2cd86786b.tar rt_ca97b9979a7b.tar rt_fb6bf34c7748.tar rt_abd1d506a71c.tar; do echo "== $t"; tar tf $t | grep -v -E '/k/|\.png$' | head -12; done
for t in rt_*.tar; do for m in $(tar tf $t | grep -E 'vxm_m4/receipt.json$'); do echo "VXM $t $m $(tar xOf $t $m | sha256sum | cut -c1-64)"; echo B64X; tar xOf $t $m | base64 -w0; echo; done; done
