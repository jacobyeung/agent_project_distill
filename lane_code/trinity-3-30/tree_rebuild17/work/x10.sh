for d in tr15_rev24l3 tr16_rev24l4r tr16_rev24l4s tr17_rev24l4t tr17_rev24l4c; do f=/scratch/jjyeung/orch_n30/$d/VERDICT.md; echo "=====$d $(sha256sum $f | cut -c1-64)"; cat $f; done
