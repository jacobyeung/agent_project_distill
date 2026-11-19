hostname -s; uptime | cut -c1-80; df -h /scratch | tail -1
R=/scratch/jjyeung/orch_n30/trin_read/root
echo "== root"; ls $R | head -40
echo "== k6tk"; ls $R/k6tk | head -4; ls $R/k6tk | wc -l
ls -la $R/k6tk/54/5434c2265b166c943c3a67b94fcecce2ac913e7349f99409826c7cf959dc177f.png $R/k6tk/7f/7f8b99bfd9565ec8a1b8fad3450c21ee4f62be29c14b5118e55764b53bc739b0.png 2>&1 | cut -c1-220
echo "== trin_read"; ls /scratch/jjyeung/orch_n30/trin_read | head -30
echo "== envs"; ls /scratch/jjyeung/envs 2>/dev/null | head -30
for p in /scratch/jjyeung/envs/*/bin/python; do timeout 20 $p -c "import PIL, sys; print(sys.argv[1], PIL.__version__)" $p 2>/dev/null; done | head -8
echo "== n30_mirror"; ls /scratch/jjyeung/n30_mirror | head -80
echo "== orch_n30"; ls /scratch/jjyeung/orch_n30 | tr '\n' ' ' | cut -c1-3000
