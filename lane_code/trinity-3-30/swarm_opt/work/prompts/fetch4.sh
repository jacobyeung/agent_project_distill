cd /scratch/jjyeung/orch_n30 && tar cf - so_git/out 2>/dev/null | base64 -w0; echo
ls -R so_git/out | head -40; ls so_git/work | head -40
