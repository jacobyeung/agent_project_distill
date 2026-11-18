cd /scratch/jjyeung/n30_mirror
ls tree_rebuild | head; ls -d tree_rebuild/*/base* tree_rebuild/*/*/tree_b01ce449 2>/dev/null | head
for f in */*.tar; do tar tf "$f" 2>/dev/null | grep -m2 -E "tree_b01ce449/|4c230a7e.json" | sed "s|^|$f: |"; done 2>/dev/null | head
ls /scratch/jjyeung/orch_n30 2>/dev/null | head -50 | tr '\n' ' '
